# Integration Architecture Guide

## Component Integration Overview

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    CLI      │  │   Output    │  │      Progress       │  │
│  │  Commands   │  │ Formatters  │  │     Tracking       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Core Engine Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Execution   │  │   Client    │  │     Result         │  │
│  │   Engine    │  │  Factory    │  │   Collector        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Operations Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Operation   │  │ Parameter   │  │      Retry         │  │
│  │  Registry   │  │Transformers │  │     Logic          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Configuration Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Pydantic  │  │    File     │  │    Validation      │  │
│  │   Models    │  │  References │  │      Engine        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Interface Definitions

### Core Interfaces

**File**: `src/s3tester/interfaces.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncIterator
from pathlib import Path
from .config.models import TestConfiguration, TestSession, TestResult
from .operations.base import OperationResult

class IConfigurationLoader(ABC):
    """Interface for configuration loading."""
    
    @abstractmethod
    def load_configuration(self, config_path: Path) -> TestConfiguration:
        """Load configuration from file."""
        pass
    
    @abstractmethod
    def validate_configuration(self, config: TestConfiguration, strict: bool = False) -> tuple[bool, List[str]]:
        """Validate configuration and return (is_valid, errors)."""
        pass

class IOperationExecutor(ABC):
    """Interface for S3 operation execution."""
    
    @abstractmethod
    def execute_operation(self, operation_name: str, parameters: Dict[str, Any], 
                         client, config_dir: Path) -> OperationResult:
        """Execute single S3 operation."""
        pass
    
    @abstractmethod
    def list_supported_operations(self) -> List[str]:
        """List all supported operation names."""
        pass

class ITestEngine(ABC):
    """Interface for test execution engine."""
    
    @abstractmethod
    async def execute_tests(self, group_names: Optional[List[str]] = None,
                          parallel: Optional[bool] = None) -> TestSession:
        """Execute test scenarios."""
        pass
    
    @abstractmethod
    def cancel(self):
        """Cancel test execution."""
        pass

class IResultFormatter(ABC):
    """Interface for result formatting."""
    
    @abstractmethod
    def format_session(self, session: TestSession) -> str:
        """Format test session results."""
        pass
    
    @abstractmethod
    def display_session(self, session: TestSession):
        """Display test session results to console."""
        pass

class IProgressTracker(ABC):
    """Interface for progress tracking."""
    
    @abstractmethod
    def start_session(self, total_groups: int, total_operations: int):
        """Start tracking session progress."""
        pass
    
    @abstractmethod
    def update_operation(self, operation_name: str, success: bool):
        """Update progress for completed operation."""
        pass
    
    @abstractmethod
    def finish_session(self):
        """Finish session progress tracking."""
        pass
```

### Data Flow Patterns

#### Configuration Flow

**File**: `src/s3tester/integration/config_flow.py`

```python
from pathlib import Path
from typing import Optional
from ..config.models import TestConfiguration
from ..core.validator import ConfigurationValidator
from ..interfaces import IConfigurationLoader

class ConfigurationFlow(IConfigurationLoader):
    """Manages configuration loading and validation flow."""
    
    def __init__(self):
        self.validator = ConfigurationValidator()
    
    def load_configuration(self, config_path: Path) -> TestConfiguration:
        """Load and validate configuration."""
        # 1. Load raw configuration
        config = TestConfiguration.load_from_file(config_path)
        
        # 2. Basic validation (already done by Pydantic)
        
        # 3. Cross-reference validation
        is_valid, errors = self.validator.validate_configuration(config, strict=False)
        if not is_valid:
            from ..exceptions import ConfigurationError
            raise ConfigurationError(f"Configuration validation failed: {'; '.join(errors)}")
        
        return config
    
    def validate_configuration(self, config: TestConfiguration, strict: bool = False) -> tuple[bool, List[str]]:
        """Validate configuration comprehensively."""
        return self.validator.validate_configuration(config, strict=strict)

class ConfigurationResolver:
    """Resolves configuration from multiple sources."""
    
    @staticmethod
    def resolve_config_path(explicit_path: Optional[Path] = None) -> Optional[Path]:
        """Resolve configuration file path from various sources."""
        import os
        
        # 1. Explicit path (highest priority)
        if explicit_path:
            return explicit_path.resolve()
        
        # 2. Environment variable
        env_config = os.getenv('S3TESTER_CONFIG')
        if env_config:
            return Path(env_config).resolve()
        
        # 3. Current directory
        for name in ['s3tester.yaml', 's3tester.yml', 'config.yaml']:
            path = Path.cwd() / name
            if path.exists():
                return path
        
        return None
```

#### Execution Flow

**File**: `src/s3tester/integration/execution_flow.py`

```python
import asyncio
from typing import List, Optional, Dict, Any
from ..config.models import TestConfiguration, TestSession
from ..core.engine import TestExecutionEngine
from ..core.progress import TestProgressTracker
from ..interfaces import ITestEngine, IProgressTracker

class ExecutionOrchestrator:
    """Orchestrates the complete test execution flow."""
    
    def __init__(self, config: TestConfiguration, 
                 progress_tracker: Optional[IProgressTracker] = None,
                 dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.progress_tracker = progress_tracker
        
        # Initialize engine
        self.engine = TestExecutionEngine(config, dry_run=dry_run)
    
    async def execute_complete_workflow(self, 
                                      group_names: Optional[List[str]] = None,
                                      parallel: Optional[bool] = None) -> TestSession:
        """Execute complete test workflow with progress tracking."""
        
        # 1. Prepare execution context
        groups = self._resolve_groups(group_names)
        execution_mode = self._resolve_execution_mode(parallel)
        
        # 2. Initialize progress tracking
        if self.progress_tracker:
            total_groups = len(groups)
            total_operations = sum(len(g.get_all_operations()) for g in groups)
            self.progress_tracker.start_session(total_groups, total_operations)
        
        try:
            # 3. Execute tests
            session = await self.engine.execute_tests(
                group_names=group_names,
                parallel=execution_mode
            )
            
            # 4. Post-process results
            self._post_process_session(session)
            
            return session
            
        finally:
            # 5. Cleanup progress tracking
            if self.progress_tracker:
                self.progress_tracker.finish_session()
    
    def _resolve_groups(self, group_names: Optional[List[str]]) -> List[TestGroup]:
        """Resolve which groups to execute."""
        if group_names:
            groups = []
            for name in group_names:
                group = self.config.test_cases.get_group(name)
                if not group:
                    raise ValueError(f"Test group not found: {name}")
                groups.append(group)
            return groups
        return self.config.test_cases.groups
    
    def _resolve_execution_mode(self, explicit_parallel: Optional[bool]) -> bool:
        """Resolve whether to execute in parallel mode."""
        if explicit_parallel is not None:
            return explicit_parallel
        return self.config.test_cases.parallel
    
    def _post_process_session(self, session: TestSession):
        """Post-process session results."""
        # Add any additional processing, logging, etc.
        pass
```

### Error Propagation Patterns

**File**: `src/s3tester/integration/error_handling.py`

```python
from typing import Optional, Dict, Any
import logging
from ..exceptions import S3TesterError, ConfigurationError, OperationError

class ErrorContext:
    """Context information for error handling."""
    
    def __init__(self, 
                 operation_name: Optional[str] = None,
                 group_name: Optional[str] = None,
                 parameters: Optional[Dict[str, Any]] = None):
        self.operation_name = operation_name
        self.group_name = group_name
        self.parameters = parameters or {}

class ErrorHandler:
    """Central error handling and logging."""
    
    def __init__(self):
        self.logger = logging.getLogger("s3tester.error_handler")
    
    def handle_configuration_error(self, error: Exception, config_path: str) -> ConfigurationError:
        """Handle and wrap configuration errors."""
        self.logger.error(f"Configuration error in {config_path}: {error}")
        
        if isinstance(error, ConfigurationError):
            return error
        
        return ConfigurationError(f"Failed to load configuration from {config_path}: {error}")
    
    def handle_operation_error(self, error: Exception, context: ErrorContext) -> OperationError:
        """Handle and wrap operation errors."""
        error_msg = (
            f"Operation {context.operation_name} failed in group {context.group_name}: {error}"
        )
        self.logger.error(error_msg)
        
        if isinstance(error, OperationError):
            return error
        
        return OperationError(error_msg, context.operation_name, context.group_name, error)
    
    def handle_engine_error(self, error: Exception, session_id: str) -> S3TesterError:
        """Handle and wrap engine errors."""
        error_msg = f"Test execution failed in session {session_id}: {error}"
        self.logger.error(error_msg)
        
        if isinstance(error, S3TesterError):
            return error
        
        return S3TesterError(error_msg, error)
    
    def log_operation_result(self, operation_name: str, group_name: str, 
                           success: bool, duration: float, error: Optional[str] = None):
        """Log operation result with consistent format."""
        status = "SUCCESS" if success else "FAILED"
        log_msg = f"{status} - {group_name}:{operation_name} ({duration:.2f}s)"
        
        if success:
            self.logger.info(log_msg)
        else:
            self.logger.warning(f"{log_msg} - {error}")
```

### Dependency Injection Patterns

**File**: `src/s3tester/integration/dependency_injection.py`

```python
from typing import Dict, Type, TypeVar, Generic, Optional
from dataclasses import dataclass
from ..interfaces import IConfigurationLoader, ITestEngine, IResultFormatter, IProgressTracker

T = TypeVar('T')

class ServiceContainer:
    """Simple dependency injection container."""
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}
    
    def register_instance(self, interface: Type[T], instance: T):
        """Register service instance."""
        self._services[interface] = instance
    
    def register_factory(self, interface: Type[T], factory: callable):
        """Register service factory."""
        self._factories[interface] = factory
    
    def get(self, interface: Type[T]) -> T:
        """Get service instance."""
        if interface in self._services:
            return self._services[interface]
        
        if interface in self._factories:
            instance = self._factories[interface]()
            self._services[interface] = instance
            return instance
        
        raise ValueError(f"Service not registered: {interface}")

@dataclass
class ApplicationContext:
    """Application context with all services."""
    
    config_loader: IConfigurationLoader
    test_engine: ITestEngine
    result_formatter: IResultFormatter
    progress_tracker: Optional[IProgressTracker] = None
    
    @classmethod
    def create_default(cls) -> 'ApplicationContext':
        """Create default application context."""
        from ..integration.config_flow import ConfigurationFlow
        from ..core.engine import TestExecutionEngine
        from ..reporting.formatters import OutputFormatter
        from ..core.progress import TestProgressTracker
        
        # Note: Some services require configuration, so this is a template
        return cls(
            config_loader=ConfigurationFlow(),
            test_engine=None,  # Created after config load
            result_formatter=OutputFormatter('table'),
            progress_tracker=TestProgressTracker()
        )

class ServiceFactory:
    """Factory for creating configured services."""
    
    @staticmethod
    def create_test_engine(config, dry_run: bool = False) -> ITestEngine:
        """Create configured test engine."""
        from ..core.engine import TestExecutionEngine
        return TestExecutionEngine(config, dry_run=dry_run)
    
    @staticmethod
    def create_result_formatter(format_type: str) -> IResultFormatter:
        """Create result formatter."""
        from ..reporting.formatters import OutputFormatter
        return OutputFormatter(format_type)
    
    @staticmethod
    def create_progress_tracker(show_progress: bool = True) -> Optional[IProgressTracker]:
        """Create progress tracker."""
        if not show_progress:
            return None
        
        from ..reporting.formatters import TestProgressTracker
        from rich.console import Console
        return TestProgressTracker(Console(), show_progress=True)
```

### Component Communication Patterns

**File**: `src/s3tester/integration/communication.py`

```python
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class Event:
    """Base event class."""
    name: str
    timestamp: datetime
    data: Dict[str, Any]

@dataclass 
class OperationStartedEvent(Event):
    """Operation execution started."""
    operation_name: str
    group_name: str
    parameters: Dict[str, Any]

@dataclass
class OperationCompletedEvent(Event):
    """Operation execution completed."""
    operation_name: str
    group_name: str
    success: bool
    duration: float
    error_message: Optional[str] = None

@dataclass
class GroupStartedEvent(Event):
    """Test group execution started."""
    group_name: str
    total_operations: int

@dataclass
class GroupCompletedEvent(Event):
    """Test group execution completed."""
    group_name: str
    passed: int
    failed: int
    error: int
    duration: float

class EventBus:
    """Simple event bus for component communication."""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._async_handlers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_name: str, handler: Callable):
        """Subscribe to synchronous events."""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
    
    def subscribe_async(self, event_name: str, handler: Callable):
        """Subscribe to asynchronous events."""
        if event_name not in self._async_handlers:
            self._async_handlers[event_name] = []
        self._async_handlers[event_name].append(handler)
    
    def publish(self, event: Event):
        """Publish synchronous event."""
        handlers = self._handlers.get(event.name, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                import logging
                logging.getLogger("event_bus").error(f"Event handler failed: {e}")
    
    async def publish_async(self, event: Event):
        """Publish asynchronous event."""
        # Handle sync handlers
        self.publish(event)
        
        # Handle async handlers
        async_handlers = self._async_handlers.get(event.name, [])
        if async_handlers:
            tasks = [handler(event) for handler in async_handlers]
            await asyncio.gather(*tasks, return_exceptions=True)

# Event handlers for different components
class ProgressEventHandler:
    """Handle events for progress tracking."""
    
    def __init__(self, progress_tracker):
        self.progress_tracker = progress_tracker
    
    def handle_operation_started(self, event: OperationStartedEvent):
        """Handle operation started event."""
        # Could update progress display
        pass
    
    def handle_operation_completed(self, event: OperationCompletedEvent):
        """Handle operation completed event."""
        if self.progress_tracker:
            self.progress_tracker.update_operation(
                event.operation_name, 
                event.success
            )
    
    def handle_group_started(self, event: GroupStartedEvent):
        """Handle group started event."""
        if self.progress_tracker:
            self.progress_tracker.start_group(
                event.group_name,
                event.total_operations
            )

class LoggingEventHandler:
    """Handle events for logging."""
    
    def __init__(self):
        import logging
        self.logger = logging.getLogger("s3tester.events")
    
    def handle_operation_completed(self, event: OperationCompletedEvent):
        """Log operation completion."""
        status = "SUCCESS" if event.success else "FAILED"
        msg = f"{status} - {event.group_name}:{event.operation_name} ({event.duration:.2f}s)"
        
        if event.success:
            self.logger.info(msg)
        else:
            self.logger.warning(f"{msg} - {event.error_message}")
    
    def handle_group_completed(self, event: GroupCompletedEvent):
        """Log group completion."""
        self.logger.info(
            f"Group '{event.group_name}' completed: "
            f"{event.passed} passed, {event.failed} failed, {event.error} errors "
            f"({event.duration:.2f}s)"
        )
```

### Integration Facade

**File**: `src/s3tester/integration/facade.py`

```python
import asyncio
from pathlib import Path
from typing import Optional, List
from rich.console import Console

from .config_flow import ConfigurationFlow, ConfigurationResolver
from .execution_flow import ExecutionOrchestrator
from .dependency_injection import ApplicationContext, ServiceFactory
from .communication import EventBus, ProgressEventHandler, LoggingEventHandler
from ..config.models import TestSession

class S3TesterFacade:
    """High-level facade for s3tester functionality."""
    
    def __init__(self, 
                 config_path: Optional[Path] = None,
                 dry_run: bool = False,
                 format_type: str = 'table',
                 show_progress: bool = True,
                 console: Optional[Console] = None):
        
        self.config_path = config_path
        self.dry_run = dry_run
        self.format_type = format_type
        self.show_progress = show_progress
        self.console = console or Console()
        
        # Initialize components
        self._setup_components()
    
    def _setup_components(self):
        """Set up all application components."""
        # Resolve configuration path
        resolved_config_path = ConfigurationResolver.resolve_config_path(self.config_path)
        if not resolved_config_path:
            raise ValueError("Configuration file not found")
        
        # Load configuration
        config_flow = ConfigurationFlow()
        self.config = config_flow.load_configuration(resolved_config_path)
        
        # Create services
        self.test_engine = ServiceFactory.create_test_engine(self.config, self.dry_run)
        self.result_formatter = ServiceFactory.create_result_formatter(self.format_type)
        self.progress_tracker = ServiceFactory.create_progress_tracker(self.show_progress)
        
        # Set up event bus
        self.event_bus = EventBus()
        self._setup_event_handlers()
        
        # Create execution orchestrator
        self.orchestrator = ExecutionOrchestrator(
            self.config, 
            self.progress_tracker,
            self.dry_run
        )
    
    def _setup_event_handlers(self):
        """Set up event handlers."""
        # Progress tracking
        if self.progress_tracker:
            progress_handler = ProgressEventHandler(self.progress_tracker)
            self.event_bus.subscribe('operation_completed', progress_handler.handle_operation_completed)
            self.event_bus.subscribe('group_started', progress_handler.handle_group_started)
        
        # Logging
        logging_handler = LoggingEventHandler()
        self.event_bus.subscribe('operation_completed', logging_handler.handle_operation_completed)
        self.event_bus.subscribe('group_completed', logging_handler.handle_group_completed)
    
    async def execute_tests(self, 
                          group_names: Optional[List[str]] = None,
                          parallel: Optional[bool] = None) -> TestSession:
        """Execute tests with full orchestration."""
        return await self.orchestrator.execute_complete_workflow(
            group_names=group_names,
            parallel=parallel
        )
    
    def validate_configuration(self, strict: bool = False) -> tuple[bool, List[str]]:
        """Validate configuration."""
        config_flow = ConfigurationFlow()
        return config_flow.validate_configuration(self.config, strict=strict)
    
    def display_results(self, session: TestSession):
        """Display results using configured formatter."""
        if self.format_type == 'table':
            from ..reporting.formatters import TableFormatter
            formatter = TableFormatter(self.console)
            formatter.display_session(session)
        else:
            formatted_output = self.result_formatter.format_session(session)
            self.console.print(formatted_output)
    
    def list_operations(self) -> List[str]:
        """List supported operations."""
        from ..operations.registry import OperationRegistry
        return OperationRegistry.list_operations()
    
    def list_groups(self) -> List[str]:
        """List configured test groups."""
        return [group.name for group in self.config.test_cases.groups]
    
    def list_credentials(self) -> List[str]:
        """List configured credentials."""
        return [cred.name for cred in self.config.config.credentials]

# Convenience function for simple usage
async def run_s3_tests(config_path: Path, 
                      group_names: Optional[List[str]] = None,
                      parallel: bool = False,
                      dry_run: bool = False,
                      format_type: str = 'table') -> TestSession:
    """Convenience function to run S3 tests."""
    
    facade = S3TesterFacade(
        config_path=config_path,
        dry_run=dry_run,
        format_type=format_type,
        show_progress=(format_type == 'table')
    )
    
    session = await facade.execute_tests(
        group_names=group_names,
        parallel=parallel
    )
    
    facade.display_results(session)
    return session
```

## Usage Examples

### Direct Integration
```python
from s3tester.integration.facade import S3TesterFacade
from pathlib import Path
import asyncio

# Create facade
facade = S3TesterFacade(
    config_path=Path("config.yaml"),
    dry_run=False,
    format_type='json'
)

# Execute tests
session = asyncio.run(facade.execute_tests(parallel=True))
print(f"Results: {session.summary.passed} passed, {session.summary.failed} failed")
```

### Service Container Usage
```python
from s3tester.integration.dependency_injection import ServiceContainer
from s3tester.interfaces import IConfigurationLoader
from s3tester.integration.config_flow import ConfigurationFlow

# Set up services
container = ServiceContainer()
container.register_instance(IConfigurationLoader, ConfigurationFlow())

# Use services
config_loader = container.get(IConfigurationLoader)
config = config_loader.load_configuration(Path("config.yaml"))
```

### Event-Driven Integration
```python
from s3tester.integration.communication import EventBus, OperationCompletedEvent

# Set up event bus
event_bus = EventBus()

def log_operation(event: OperationCompletedEvent):
    print(f"Operation {event.operation_name}: {'SUCCESS' if event.success else 'FAILED'}")

event_bus.subscribe('operation_completed', log_operation)

# Events are published automatically by the execution engine
```

## Integration Benefits

1. **Loose Coupling**: Components communicate through interfaces and events
2. **Testability**: Each component can be tested independently with mocks
3. **Extensibility**: New components can be added without modifying existing ones
4. **Configuration**: Centralized configuration management with validation
5. **Error Handling**: Consistent error propagation and handling patterns
6. **Performance**: Event-driven architecture enables efficient async processing

## Next Steps

The integration architecture provides:
1. **Complete Application Assembly**: All components work together seamlessly
2. **Extension Points**: Clear interfaces for adding new functionality
3. **Error Management**: Comprehensive error handling and logging
4. **Performance Optimization**: Event-driven async architecture
5. **Testing Support**: Dependency injection enables easy component mocking
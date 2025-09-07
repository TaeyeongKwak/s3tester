"""
Core interfaces for s3tester components.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, TextIO, Union
from pathlib import Path

# Import models but handle possible circular imports
try:
    from .config.models import S3TestConfiguration, S3TestSession, S3TestResult
    from .operations.base import OperationResult
except ImportError:
    # For type annotations only
    S3TestConfiguration = 'S3TestConfiguration'
    S3TestSession = 'S3TestSession'
    S3TestResult = 'S3TestResult'
    OperationResult = 'OperationResult'


class IConfigurationLoader(ABC):
    """Interface for configuration loading."""
    
    @abstractmethod
    def load_configuration(self, config_path: Path) -> S3TestConfiguration:
        """Load configuration from file."""
        pass
    
    @abstractmethod
    def validate_configuration(self, config: S3TestConfiguration, strict: bool = False) -> Tuple[bool, List[str]]:
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
                          parallel: Optional[bool] = None) -> S3TestSession:
        """Execute test scenarios."""
        pass
    
    @abstractmethod
    def cancel(self):
        """Cancel test execution."""
        pass


class IResultFormatter(ABC):
    """Interface for result formatting."""
    
    @abstractmethod
    def format_session(self, session: S3TestSession, output: Optional[TextIO] = None) -> None:
        """Format test session results."""
        pass
    
    @abstractmethod
    def format_result(self, result: S3TestResult, output: Optional[TextIO] = None) -> None:
        """Format a single test result."""
        pass


class IProgressTracker(ABC):
    """Interface for progress tracking."""
    
    @abstractmethod
    def start_session(self, total_groups: int, total_operations: int):
        """Start tracking session progress."""
        pass
    
    @abstractmethod
    def start_group(self, group_name: str, operations_count: int):
        """Start tracking group progress."""
        pass
    
    @abstractmethod
    def update_operation(self, operation_name: str, success: bool):
        """Update progress for completed operation."""
        pass
    
    @abstractmethod
    def finish_group(self, group_name: str):
        """Finish group progress tracking."""
        pass
    
    @abstractmethod
    def finish_session(self):
        """Finish session progress tracking."""
        pass


class IClientFactory(ABC):
    """Interface for S3 client factory."""
    
    @abstractmethod
    def create_client(self, credential):
        """Create S3 client with specified credentials."""
        pass
    
    @abstractmethod
    def test_client_connection(self, credential) -> bool:
        """Test client connection with simple operation."""
        pass
    
    @abstractmethod
    def clear_cache(self):
        """Clear client cache."""
        pass

"""
Integration facade for s3tester.
"""
import asyncio
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from rich.console import Console

from ..config.models import S3TestConfiguration, S3TestSession
from ..core.engine import S3TestExecutionEngine
from ..core.validator import ConfigurationValidator
from ..core.client_factory import S3ClientFactory
from ..reporting.formatters import get_formatter, OutputFormat
from ..operations.registry import OperationRegistry
from .error_handling import ErrorHandler, ErrorContext


class S3TesterFacade:
    """High-level facade for s3tester functionality."""
    
    def __init__(
        self, 
        config_path: Optional[Path] = None,
        dry_run: bool = False,
        format_type: str = 'CONSOLE',
        show_progress: bool = True,
        console: Optional[Console] = None
    ):
        self.config_path = config_path
        self.dry_run = dry_run
        self.format_type = format_type.upper()
        self.show_progress = show_progress
        self.console = console or Console()
        
        # Initialize components
        self.error_handler = ErrorHandler()
        self._setup_components()
    
    def _setup_components(self):
        """Set up all application components."""
        # Resolve configuration path
        resolved_config_path = self._resolve_config_path(self.config_path)
        if not resolved_config_path:
            raise ValueError("Configuration file not found")
        
        # Load configuration
        self.config = self._load_configuration(resolved_config_path)
        
        # Create services
        self.client_factory = S3ClientFactory(self.config.config)
        self.test_engine = S3TestExecutionEngine(self.config, dry_run=self.dry_run)
        self.formatter = get_formatter(self.format_type)
    
    def _resolve_config_path(self, config_path: Optional[Path]) -> Optional[Path]:
        """Resolve configuration file path from various sources."""
        import os
        
        # 1. Explicit path (highest priority)
        if config_path:
            return config_path.resolve()
        
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
    
    def _load_configuration(self, config_path: Path) -> S3TestConfiguration:
        """Load and validate configuration."""
        try:
            # 1. Load raw configuration
            config = S3TestConfiguration.load_from_file(config_path)
            
            # 2. Basic validation (already done by Pydantic)
            
            # 3. Validate configuration
            validator = ConfigurationValidator()
            is_valid, errors = validator.validate_configuration(config, strict=False)
            
            if not is_valid:
                from ..exceptions import ConfigurationError
                raise ConfigurationError(
                    f"Configuration validation failed: {'; '.join(errors)}",
                    config_path=str(config_path)
                )
            
            return config
            
        except Exception as e:
            # Handle configuration errors
            raise self.error_handler.handle_configuration_error(e, str(config_path))
    
    async def execute_tests(
        self, 
        group_names: Optional[List[str]] = None,
        parallel: Optional[bool] = None
    ) -> S3TestSession:
        """Execute tests with full orchestration."""
        try:
            return await self.test_engine.execute_tests(
                group_names=group_names,
                parallel=parallel
            )
        except Exception as e:
            session_id = getattr(self.test_engine.session, 'session_id', 'unknown')
            raise self.error_handler.handle_engine_error(e, session_id)
    
    def validate_configuration(self, strict: bool = False) -> Tuple[bool, List[str]]:
        """Validate configuration."""
        validator = ConfigurationValidator()
        return validator.validate_configuration(self.config, strict=strict)
    
    def display_results(self, session: S3TestSession):
        """Display results using configured formatter."""
        self.formatter.format_session(session)
    
    def list_operations(self) -> List[str]:
        """List supported operations."""
        return OperationRegistry.list_operations()
    
    def list_groups(self) -> List[str]:
        """List configured test groups."""
        return [group.name for group in self.config.test_cases.groups]
    
    def list_credentials(self) -> List[str]:
        """List configured credentials."""
        return [cred.name for cred in self.config.config.credentials]
    
    def get_operation_parameters(self, operation_name: str) -> Dict[str, Any]:
        """Get the expected parameters for an operation."""
        operation_class = OperationRegistry.get_operation(operation_name)
        if not operation_class:
            raise ValueError(f"Unsupported operation: {operation_name}")
        
        # Extract parameter information from the operation class
        return getattr(operation_class, 'PARAMETERS', {})


# Convenience function for simple usage
async def run_s3_tests(
    config_path: Path, 
    group_names: Optional[List[str]] = None,
    parallel: bool = False,
    dry_run: bool = False,
    format_type: str = 'console'
) -> S3TestSession:
    """Convenience function to run S3 tests."""
    
    facade = S3TesterFacade(
        config_path=config_path,
        dry_run=dry_run,
        format_type=format_type,
        show_progress=(format_type.upper() == 'CONSOLE')
    )
    
    session = await facade.execute_tests(
        group_names=group_names,
        parallel=parallel
    )
    
    facade.display_results(session)
    return session

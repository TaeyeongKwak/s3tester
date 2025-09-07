"""
Error handling patterns for s3tester.
"""
from typing import Optional, Dict, Any, Type, Union
from contextlib import contextmanager
import traceback

from ..exceptions import S3TesterError, ConfigurationError, OperationError, ExecutionError
from ..core.logging_config import get_logger, log_operation_error


class ErrorContext:
    """Context information for error handling."""
    
    def __init__(
        self, 
        operation_name: Optional[str] = None,
        group_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ):
        self.operation_name = operation_name
        self.group_name = group_name
        self.parameters = parameters or {}


class ErrorHandler:
    """Central error handling and logging."""
    
    def __init__(self):
        self.logger = get_logger("integration.error_handler")
    
    def handle_configuration_error(self, error: Exception, config_path: str) -> ConfigurationError:
        """Handle and wrap configuration errors."""
        self.logger.error(f"Configuration error in {config_path}: {error}")
        
        if isinstance(error, ConfigurationError):
            return error
        
        return ConfigurationError(f"Failed to load configuration from {config_path}: {error}", 
                                 config_path=config_path, 
                                 cause=error)
    
    def handle_operation_error(self, error: Exception, context: ErrorContext) -> OperationError:
        """Handle and wrap operation errors."""
        error_msg = (
            f"Operation {context.operation_name} failed in group {context.group_name}: {error}"
        )
        self.logger.error(error_msg)
        
        if isinstance(error, OperationError):
            return error
        
        return OperationError(
            error_msg, 
            operation_name=context.operation_name, 
            group_name=context.group_name,
            cause=error,
            parameters=context.parameters
        )
    
    def handle_engine_error(self, error: Exception, session_id: str) -> S3TesterError:
        """Handle and wrap engine errors."""
        error_msg = f"Test execution failed in session {session_id}: {error}"
        self.logger.error(error_msg)
        
        if isinstance(error, S3TesterError):
            return error
        
        from ..exceptions import ExecutionError
        return ExecutionError(error_msg, session_id=session_id, cause=error)
    
    @contextmanager
    def handle_operation_context(self, operation_name: str, group_name: str = None, **kwargs):
        """Context manager for consistent operation error handling.
        
        Args:
            operation_name: Name of the operation being performed
            group_name: Optional group name for context
            **kwargs: Additional context parameters
            
        Yields:
            None
            
        Raises:
            OperationError: If any exception occurs during the operation
            
        Example:
            >>> with error_handler.handle_operation_context("PutObject", bucket="test"):
            ...     s3_client.put_object(...)
        """
        context = ErrorContext(operation_name, group_name, kwargs)
        try:
            yield
        except Exception as e:
            raise self.handle_operation_error(e, context)
    
    @contextmanager  
    def handle_configuration_context(self, config_path: str):
        """Context manager for consistent configuration error handling.
        
        Args:
            config_path: Path to configuration file
            
        Yields:
            None
            
        Raises:
            ConfigurationError: If any exception occurs during configuration loading
            
        Example:
            >>> with error_handler.handle_configuration_context("/path/to/config.json"):
            ...     config = load_config(...)
        """
        try:
            yield
        except Exception as e:
            raise self.handle_configuration_error(e, config_path)
    
    def wrap_exception(
        self, 
        error: Exception, 
        wrapper_class: Type[S3TesterError],
        message: str = None,
        **kwargs
    ) -> S3TesterError:
        """Wrap any exception in a s3tester exception with context.
        
        Args:
            error: Original exception to wrap
            wrapper_class: Exception class to wrap with
            message: Optional custom error message  
            **kwargs: Additional context to pass to exception
            
        Returns:
            Wrapped s3tester exception
        """
        if isinstance(error, S3TesterError):
            return error
            
        final_message = message or f"{wrapper_class.__name__}: {error}"
        
        # Add traceback info for debugging
        if hasattr(error, '__traceback__') and error.__traceback__:
            tb_lines = traceback.format_tb(error.__traceback__)
            kwargs['traceback'] = ''.join(tb_lines[-3:])  # Last 3 frames
            
        return wrapper_class(final_message, cause=error, **kwargs)
    
    def log_and_reraise(
        self, 
        error: Exception, 
        operation: str, 
        level: str = "error",
        **context
    ) -> None:
        """Log an error with context and reraise it.
        
        Args:
            error: Exception to log and reraise
            operation: Operation name for context
            level: Log level (error, warning, info, debug)
            **context: Additional context for logging
            
        Raises:
            The original exception after logging
        """
        log_func = getattr(self.logger, level.lower(), self.logger.error)
        log_func(f"{operation} failed: {error}", extra={
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context
        }, exc_info=True)
        
        raise error
    
    def log_operation_result(
        self, 
        operation_name: str, 
        group_name: str, 
        success: bool, 
        duration: float, 
        error: Optional[str] = None
    ):
        """Log operation result with consistent format."""
        status = "SUCCESS" if success else "FAILED"
        log_msg = f"{status} - {group_name}:{operation_name} ({duration:.2f}s)"
        
        if success:
            self.logger.info(log_msg)
        else:
            self.logger.warning(f"{log_msg} - {error}")
            
    def format_error_details(self, error: Exception) -> str:
        """Format detailed error message for display."""
        if isinstance(error, OperationError):
            details = [
                f"Operation: {error.operation_name}",
                f"Group: {error.group_name}" if error.group_name else None,
                f"Parameters: {error.parameters}" if error.parameters else None,
                f"Cause: {error.cause}" if error.cause else None,
            ]
            return "\n".join([d for d in details if d])
        
        if isinstance(error, ConfigurationError):
            details = [
                f"Config path: {error.config_path}" if error.config_path else None,
                f"Cause: {error.cause}" if error.cause else None,
            ]
            return "\n".join([d for d in details if d])
            
        if isinstance(error, ExecutionError):
            details = [
                f"Session ID: {error.session_id}" if error.session_id else None,
                f"Cause: {error.cause}" if error.cause else None,
            ]
            return "\n".join([d for d in details if d])
            
        return str(error)

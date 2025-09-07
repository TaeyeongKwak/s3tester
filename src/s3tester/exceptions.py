"""
Exception classes for s3tester.
"""
from typing import Any, Dict, Optional


class S3TesterError(Exception):
    """Base exception for all s3tester errors."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause
        super().__init__(message)


class ConfigurationError(S3TesterError):
    """Raised when configuration loading or validation fails."""
    
    def __init__(self, message: str, config_path: Optional[str] = None, cause: Optional[Exception] = None):
        self.config_path = config_path
        super().__init__(message, cause)


class OperationError(S3TesterError):
    """Raised when an S3 operation fails."""
    
    def __init__(
        self, 
        message: str, 
        operation_name: str, 
        group_name: Optional[str] = None,
        cause: Optional[Exception] = None, 
        parameters: Optional[Dict[str, Any]] = None
    ):
        self.operation_name = operation_name
        self.group_name = group_name
        self.parameters = parameters or {}
        super().__init__(message, cause)


class ValidationError(S3TesterError):
    """Raised when validation fails."""
    
    def __init__(self, message: str, errors: Optional[list] = None):
        self.errors = errors or []
        super().__init__(message)


class ExecutionError(S3TesterError):
    """Raised when test execution fails."""
    
    def __init__(
        self,
        message: str, 
        session_id: Optional[str] = None, 
        cause: Optional[Exception] = None
    ):
        self.session_id = session_id
        super().__init__(message, cause)

"""Base classes for S3 operations.

This module provides the core infrastructure for implementing S3 operations
including base classes, context management, and result handling.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import time
from pathlib import Path

from ..core.logging_config import get_logger, log_operation_start, log_operation_success, log_operation_error


@dataclass
class OperationContext:
    """Context for operation execution.
    
    Contains all necessary information for executing an S3 operation,
    including the S3 client, parameters, and execution environment.
    
    Attributes:
        s3_client: Configured boto3 S3 client for API calls
        operation_name: Name of the operation being executed
        parameters: Dictionary of operation parameters
        config_dir: Directory containing configuration files for relative path resolution
        dry_run: If True, operation should be simulated without actual API calls
    """
    s3_client: boto3.client
    operation_name: str
    parameters: Dict[str, Any]
    config_dir: Path
    dry_run: bool = False


@dataclass 
class OperationResult:
    """Result of operation execution.
    
    Contains the outcome of an S3 operation execution including
    success status, timing, response data, and error information.
    
    Attributes:
        success: True if operation completed successfully, False otherwise
        duration: Execution time in seconds
        response: Raw response from S3 API (if successful)
        error_code: Error code from S3 API (if failed)
        error_message: Human-readable error message (if failed)
        raw_exception: Original exception that caused failure (if any)
    """
    success: bool
    duration: float
    response: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    raw_exception: Optional[Exception] = None


class S3Operation(ABC):
    """Base class for S3 operation implementations."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.logger = get_logger(f"operations.{operation_name}")
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and transform parameters for the operation."""
        pass
    
    @abstractmethod
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute the S3 operation."""
        pass
    
    def execute(self, context: OperationContext) -> OperationResult:
        """Main execution method with error handling and timing."""
        start_time = time.time()
        
        log_operation_start(self.logger, self.operation_name, parameters=context.parameters)
        
        try:
            # Parameter validation and transformation
            validated_params = self.validate_parameters(context.parameters)
            context = OperationContext(
                s3_client=context.s3_client,
                operation_name=context.operation_name,
                parameters=validated_params,
                config_dir=context.config_dir,
                dry_run=context.dry_run
            )
            
            # Dry run check
            if context.dry_run:
                duration = time.time() - start_time
                log_operation_success(self.logger, f"{self.operation_name} (DRY RUN)", duration, 
                                    parameters=validated_params)
                return OperationResult(
                    success=True,
                    duration=duration,
                    response={"dry_run": True}
                )
            
            # Execute operation
            result = self.execute_operation(context)
            result.duration = time.time() - start_time
            
            if result.success:
                log_operation_success(self.logger, self.operation_name, result.duration)
            else:
                log_operation_error(self.logger, self.operation_name, 
                                  Exception(result.error_message or "Unknown error"), 
                                  result.duration)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            log_operation_error(self.logger, self.operation_name, e, duration)
            
            return OperationResult(
                success=False,
                duration=duration,
                error_message=str(e),
                raw_exception=e
            )

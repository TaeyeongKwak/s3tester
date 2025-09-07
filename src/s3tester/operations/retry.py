"""Retry logic for S3 operations.

This module provides retry functionality for S3 operations,
implementing exponential backoff and error classification.
"""

import time
import random
import logging
from functools import wraps
from typing import Callable, Set, Optional
from botocore.exceptions import ClientError
from .base import S3Operation, OperationContext, OperationResult
from ..constants import (
    DEFAULT_MAX_RETRIES, DEFAULT_BASE_DELAY, DEFAULT_MAX_DELAY,
    DEFAULT_EXPONENTIAL_FACTOR, DEFAULT_RETRY_JITTER
)


logger = logging.getLogger(__name__)

# Error codes that should trigger retries
RETRYABLE_ERROR_CODES = {
    'SlowDown',
    'ServiceUnavailable', 
    'RequestTimeout',
    'InternalError',
    'ThrottlingException'
}

# Error codes that should never be retried
NON_RETRYABLE_ERROR_CODES = {
    'AccessDenied',
    'InvalidAccessKeyId', 
    'InvalidSecurity',
    'SignatureDoesNotMatch',
    'TokenRefreshRequired',
    'NoSuchBucket',
    'NoSuchKey',
    'InvalidBucketName',
    'BucketAlreadyExists',
    'BucketAlreadyOwnedByYou'
}


def retry_with_exponential_backoff(
    max_retries: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    exponential_factor: Optional[float] = None,
    jitter: Optional[bool] = None
):
    """Decorator for exponential backoff retry logic."""
    # Use constants as defaults if not provided
    actual_max_retries = max_retries if max_retries is not None else DEFAULT_MAX_RETRIES
    actual_base_delay = base_delay if base_delay is not None else DEFAULT_BASE_DELAY
    actual_max_delay = max_delay if max_delay is not None else DEFAULT_MAX_DELAY
    actual_exponential_factor = exponential_factor if exponential_factor is not None else DEFAULT_EXPONENTIAL_FACTOR
    actual_jitter = jitter if jitter is not None else DEFAULT_RETRY_JITTER
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(actual_max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    last_exception = e
                    
                    # Don't retry non-retryable errors
                    if error_code in NON_RETRYABLE_ERROR_CODES:
                        logger.debug(f"Non-retryable error {error_code}, not retrying")
                        raise
                    
                    # Don't retry on last attempt
                    if attempt == actual_max_retries:
                        logger.debug(f"Max retries ({actual_max_retries}) reached")
                        raise
                    
                    # Only retry specific error codes
                    if error_code not in RETRYABLE_ERROR_CODES:
                        logger.debug(f"Error {error_code} not in retryable list")
                        raise
                    
                    # Calculate delay
                    delay = min(
                        actual_base_delay * (actual_exponential_factor ** attempt),
                        actual_max_delay
                    )
                    
                    if actual_jitter:
                        delay *= (0.5 + random.random() / 2)
                    
                    logger.warning(
                        f"Retrying {func.__name__} after {delay:.2f}s "
                        f"(attempt {attempt + 1}/{actual_max_retries + 1}) "
                        f"due to {error_code}: {e.response['Error']['Message']}"
                    )
                    
                    time.sleep(delay)
                    
                except Exception as e:
                    # For non-ClientError exceptions, only retry on first few attempts
                    last_exception = e
                    
                    if attempt >= 2:  # Allow 2 retries for general exceptions
                        logger.debug(f"General exception after {attempt} attempts: {e}")
                        raise
                    
                    delay = base_delay * (exponential_factor ** attempt)
                    if jitter:
                        delay *= (0.5 + random.random() / 2)
                    
                    logger.warning(f"Retrying {func.__name__} after {delay:.2f}s due to: {e}")
                    time.sleep(delay)
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


class RetryableS3Operation(S3Operation):
    """Base class for S3 operations with built-in retry logic."""
    
    @retry_with_exponential_backoff(max_retries=3)
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute operation with retry logic."""
        return super().execute_operation(context)

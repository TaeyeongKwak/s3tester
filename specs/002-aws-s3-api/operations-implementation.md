# S3 Operations Implementation Guide

## Operation Execution Architecture

### Core Operation Interface

**File**: `src/s3tester/operations/base.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import time
import logging

@dataclass
class OperationContext:
    """Context for operation execution."""
    s3_client: boto3.client
    operation_name: str
    parameters: Dict[str, Any]
    config_dir: Path
    dry_run: bool = False

@dataclass 
class OperationResult:
    """Result of operation execution."""
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
        self.logger = logging.getLogger(f"s3tester.operations.{operation_name}")
    
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
        
        try:
            # Parameter validation and transformation
            validated_params = self.validate_parameters(context.parameters)
            context = context.__class__(
                **{**context.__dict__, 'parameters': validated_params}
            )
            
            # Dry run check
            if context.dry_run:
                self.logger.info(f"DRY RUN: {self.operation_name} with {validated_params}")
                return OperationResult(
                    success=True,
                    duration=0.0,
                    response={"dry_run": True}
                )
            
            # Execute operation
            result = self.execute_operation(context)
            result.duration = time.time() - start_time
            
            self.logger.info(
                f"{self.operation_name} completed in {result.duration:.2f}s "
                f"(success={result.success})"
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"{self.operation_name} failed after {duration:.2f}s: {e}")
            
            return OperationResult(
                success=False,
                duration=duration,
                error_message=str(e),
                raw_exception=e
            )
```

### Parameter Transformation Patterns

**File**: `src/s3tester/operations/parameters.py`

```python
from pathlib import Path
from typing import Dict, Any, Union
from ..config.models import FileReference

class ParameterTransformer:
    """Transform YAML parameters to boto3 format."""
    
    @staticmethod
    def transform_file_reference(value: Union[str, FileReference], 
                               config_dir: Path) -> bytes:
        """Transform file:// reference to file content."""
        if isinstance(value, str):
            if value.startswith('file://'):
                file_ref = FileReference.from_path_spec(value, config_dir)
            else:
                # Treat as literal string content
                return value.encode('utf-8')
        else:
            file_ref = value
        
        if not file_ref.exists:
            raise FileNotFoundError(f"Referenced file not found: {file_ref.resolved_path}")
        
        return file_ref.read_content()
    
    @staticmethod  
    def transform_bucket_name(bucket: str) -> str:
        """Validate and transform bucket name."""
        import re
        
        # AWS S3 bucket naming rules
        if not re.match(r'^[a-z0-9][a-z0-9.-]*[a-z0-9]$', bucket):
            raise ValueError(f"Invalid bucket name format: {bucket}")
        
        if len(bucket) < 3 or len(bucket) > 63:
            raise ValueError(f"Bucket name length must be 3-63 characters: {bucket}")
            
        if '..' in bucket:
            raise ValueError(f"Bucket name cannot contain consecutive periods: {bucket}")
            
        return bucket
    
    @staticmethod
    def transform_object_key(key: str) -> str:
        """Validate and transform object key."""
        if not key or len(key) > 1024:
            raise ValueError(f"Object key length must be 1-1024 characters: {key}")
        return key
    
    @staticmethod
    def transform_tagging(tags: Dict[str, str]) -> str:
        """Transform tag dictionary to S3 tagging string format."""
        if not tags:
            return ""
        
        tag_pairs = []
        for key, value in tags.items():
            # URL encode key and value
            from urllib.parse import quote
            encoded_key = quote(str(key), safe='')
            encoded_value = quote(str(value), safe='')
            tag_pairs.append(f"{encoded_key}={encoded_value}")
        
        return "&".join(tag_pairs)
```

### Bucket Operations Implementation

**File**: `src/s3tester/operations/bucket.py`

```python
from typing import Dict, Any
from botocore.exceptions import ClientError
from .base import S3Operation, OperationContext, OperationResult
from .parameters import ParameterTransformer

class CreateBucketOperation(S3Operation):
    """Create S3 bucket operation."""
    
    def __init__(self):
        super().__init__("CreateBucket")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate CreateBucket parameters."""
        if 'bucket' not in parameters:
            raise ValueError("CreateBucket requires 'bucket' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        
        validated = {'Bucket': bucket}
        
        # Handle region-specific bucket creation
        if 'region' in parameters and parameters['region'] != 'us-east-1':
            validated['CreateBucketConfiguration'] = {
                'LocationConstraint': parameters['region']
            }
        
        # Handle ACL if specified
        if 'acl' in parameters:
            validated['ACL'] = parameters['acl']
            
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute CreateBucket operation."""
        try:
            response = context.s3_client.create_bucket(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,  # Will be set by base class
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            # Handle expected errors
            if error_code in ['BucketAlreadyExists', 'BucketAlreadyOwnedByYou']:
                return OperationResult(
                    success=False,
                    duration=0.0,
                    error_code=error_code,
                    error_message=e.response['Error']['Message'],
                    response=e.response
                )
            
            # Re-raise unexpected errors
            raise

class DeleteBucketOperation(S3Operation):
    """Delete S3 bucket operation."""
    
    def __init__(self):
        super().__init__("DeleteBucket")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate DeleteBucket parameters."""
        if 'bucket' not in parameters:
            raise ValueError("DeleteBucket requires 'bucket' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        return {'Bucket': bucket}
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute DeleteBucket operation."""
        try:
            response = context.s3_client.delete_bucket(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            # Handle expected errors
            if error_code in ['NoSuchBucket', 'BucketNotEmpty']:
                return OperationResult(
                    success=False,
                    duration=0.0,
                    error_code=error_code,
                    error_message=e.response['Error']['Message'],
                    response=e.response
                )
            
            raise

class ListBucketsOperation(S3Operation):
    """List S3 buckets operation."""
    
    def __init__(self):
        super().__init__("ListBuckets")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ListBuckets parameters (none required)."""
        return {}
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute ListBuckets operation."""
        try:
            response = context.s3_client.list_buckets()
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=e.response['Error']['Message'],
                response=e.response
            )
```

### Object Operations Implementation

**File**: `src/s3tester/operations/object.py`

```python
from typing import Dict, Any, Union
from botocore.exceptions import ClientError
from .base import S3Operation, OperationContext, OperationResult
from .parameters import ParameterTransformer
from ..config.models import FileReference

class PutObjectOperation(S3Operation):
    """Put object to S3 operation."""
    
    def __init__(self):
        super().__init__("PutObject")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PutObject parameters."""
        required_params = ['bucket', 'key']
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"PutObject requires '{param}' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        key = ParameterTransformer.transform_object_key(parameters['key'])
        
        validated = {
            'Bucket': bucket,
            'Key': key
        }
        
        # Handle body content
        if 'body' in parameters:
            if isinstance(parameters['body'], (str, FileReference)):
                validated['Body'] = ParameterTransformer.transform_file_reference(
                    parameters['body'], 
                    parameters.get('_config_dir', Path.cwd())
                )
            else:
                validated['Body'] = parameters['body']
        
        # Handle metadata
        if 'metadata' in parameters:
            validated['Metadata'] = parameters['metadata']
            
        # Handle content type
        if 'content_type' in parameters:
            validated['ContentType'] = parameters['content_type']
            
        # Handle tagging
        if 'tags' in parameters:
            validated['Tagging'] = ParameterTransformer.transform_tagging(parameters['tags'])
        
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute PutObject operation."""
        try:
            response = context.s3_client.put_object(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            # Handle expected errors
            if error_code in ['NoSuchBucket', 'AccessDenied', 'InvalidBucketName']:
                return OperationResult(
                    success=False,
                    duration=0.0,
                    error_code=error_code,
                    error_message=e.response['Error']['Message'],
                    response=e.response
                )
            
            raise

class GetObjectOperation(S3Operation):
    """Get object from S3 operation."""
    
    def __init__(self):
        super().__init__("GetObject")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GetObject parameters."""
        required_params = ['bucket', 'key']
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"GetObject requires '{param}' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        key = ParameterTransformer.transform_object_key(parameters['key'])
        
        validated = {
            'Bucket': bucket,
            'Key': key
        }
        
        # Handle version ID
        if 'version_id' in parameters:
            validated['VersionId'] = parameters['version_id']
            
        # Handle range requests
        if 'range' in parameters:
            validated['Range'] = parameters['range']
        
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute GetObject operation."""
        try:
            response = context.s3_client.get_object(**context.parameters)
            
            # For testing purposes, read body content
            if 'Body' in response:
                body_content = response['Body'].read()
                response['Body'] = body_content
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            # Handle expected errors
            if error_code in ['NoSuchKey', 'NoSuchBucket', 'AccessDenied']:
                return OperationResult(
                    success=False,
                    duration=0.0,
                    error_code=error_code,
                    error_message=e.response['Error']['Message'],
                    response=e.response
                )
            
            raise

class DeleteObjectOperation(S3Operation):
    """Delete object from S3 operation."""
    
    def __init__(self):
        super().__init__("DeleteObject")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate DeleteObject parameters."""
        required_params = ['bucket', 'key']
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"DeleteObject requires '{param}' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        key = ParameterTransformer.transform_object_key(parameters['key'])
        
        validated = {
            'Bucket': bucket,
            'Key': key
        }
        
        # Handle version ID
        if 'version_id' in parameters:
            validated['VersionId'] = parameters['version_id']
        
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute DeleteObject operation."""
        try:
            response = context.s3_client.delete_object(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            # Note: S3 returns success even for non-existent objects
            # Only actual errors should be handled here
            if error_code in ['AccessDenied', 'NoSuchBucket']:
                return OperationResult(
                    success=False,
                    duration=0.0,
                    error_code=error_code,
                    error_message=e.response['Error']['Message'],
                    response=e.response
                )
            
            raise
```

### Multipart Upload Operations

**File**: `src/s3tester/operations/multipart.py`

```python
class CreateMultipartUploadOperation(S3Operation):
    """Create multipart upload operation."""
    
    def __init__(self):
        super().__init__("CreateMultipartUpload")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate CreateMultipartUpload parameters."""
        required_params = ['bucket', 'key']
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"CreateMultipartUpload requires '{param}' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        key = ParameterTransformer.transform_object_key(parameters['key'])
        
        validated = {
            'Bucket': bucket,
            'Key': key
        }
        
        # Handle optional parameters
        optional_params = {
            'metadata': 'Metadata',
            'content_type': 'ContentType',
            'cache_control': 'CacheControl',
            'content_disposition': 'ContentDisposition',
            'content_encoding': 'ContentEncoding',
            'content_language': 'ContentLanguage'
        }
        
        for yaml_param, boto_param in optional_params.items():
            if yaml_param in parameters:
                validated[boto_param] = parameters[yaml_param]
        
        # Handle tagging
        if 'tags' in parameters:
            validated['Tagging'] = ParameterTransformer.transform_tagging(parameters['tags'])
        
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute CreateMultipartUpload operation."""
        try:
            response = context.s3_client.create_multipart_upload(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code in ['NoSuchBucket', 'AccessDenied']:
                return OperationResult(
                    success=False,
                    duration=0.0,
                    error_code=error_code,
                    error_message=e.response['Error']['Message'],
                    response=e.response
                )
            
            raise

class UploadPartOperation(S3Operation):
    """Upload part for multipart upload operation."""
    
    def __init__(self):
        super().__init__("UploadPart")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate UploadPart parameters."""
        required_params = ['bucket', 'key', 'upload_id', 'part_number']
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"UploadPart requires '{param}' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        key = ParameterTransformer.transform_object_key(parameters['key'])
        
        # Validate part number
        part_number = int(parameters['part_number'])
        if not (1 <= part_number <= 10000):
            raise ValueError(f"Part number must be between 1 and 10000: {part_number}")
        
        validated = {
            'Bucket': bucket,
            'Key': key,
            'UploadId': parameters['upload_id'],
            'PartNumber': part_number
        }
        
        # Handle body content
        if 'body' in parameters:
            if isinstance(parameters['body'], (str, FileReference)):
                validated['Body'] = ParameterTransformer.transform_file_reference(
                    parameters['body'],
                    parameters.get('_config_dir', Path.cwd())
                )
            else:
                validated['Body'] = parameters['body']
        
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute UploadPart operation."""
        try:
            response = context.s3_client.upload_part(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code in ['NoSuchUpload', 'InvalidPart', 'InvalidPartOrder']:
                return OperationResult(
                    success=False,
                    duration=0.0,
                    error_code=error_code,
                    error_message=e.response['Error']['Message'],
                    response=e.response
                )
            
            raise
```

### Operation Registry and Factory

**File**: `src/s3tester/operations/registry.py`

```python
from typing import Dict, Type
from .base import S3Operation
from .bucket import CreateBucketOperation, DeleteBucketOperation, ListBucketsOperation
from .object import PutObjectOperation, GetObjectOperation, DeleteObjectOperation
from .multipart import CreateMultipartUploadOperation, UploadPartOperation

class OperationRegistry:
    """Registry for S3 operation implementations."""
    
    _operations: Dict[str, Type[S3Operation]] = {}
    
    @classmethod
    def register(cls, operation_name: str, operation_class: Type[S3Operation]):
        """Register an operation implementation."""
        cls._operations[operation_name] = operation_class
    
    @classmethod
    def get_operation(cls, operation_name: str) -> S3Operation:
        """Get operation instance by name."""
        if operation_name not in cls._operations:
            raise ValueError(f"Unsupported operation: {operation_name}")
        
        operation_class = cls._operations[operation_name]
        return operation_class()
    
    @classmethod
    def list_operations(cls) -> List[str]:
        """List all registered operation names."""
        return list(cls._operations.keys())

# Register all operations
def register_operations():
    """Register all built-in operations."""
    registry = OperationRegistry
    
    # Bucket operations
    registry.register("CreateBucket", CreateBucketOperation)
    registry.register("DeleteBucket", DeleteBucketOperation)
    registry.register("ListBuckets", ListBucketsOperation)
    
    # Object operations
    registry.register("PutObject", PutObjectOperation)
    registry.register("GetObject", GetObjectOperation)
    registry.register("DeleteObject", DeleteObjectOperation)
    
    # Multipart operations
    registry.register("CreateMultipartUpload", CreateMultipartUploadOperation)
    registry.register("UploadPart", UploadPartOperation)
    
    # Add more operations as needed...

# Auto-register on import
register_operations()

# Export supported operations for validation
SUPPORTED_OPERATIONS = OperationRegistry.list_operations()
```

### Error Handling and Retry Logic

**File**: `src/s3tester/operations/retry.py`

```python
import time
import random
from functools import wraps
from typing import Callable, Set
from botocore.exceptions import ClientError
import logging

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
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_factor: float = 2.0,
    jitter: bool = True
):
    """Decorator for exponential backoff retry logic."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
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
                    if attempt == max_retries:
                        logger.debug(f"Max retries ({max_retries}) reached")
                        raise
                    
                    # Only retry specific error codes
                    if error_code not in RETRYABLE_ERROR_CODES:
                        logger.debug(f"Error {error_code} not in retryable list")
                        raise
                    
                    # Calculate delay
                    delay = min(
                        base_delay * (exponential_factor ** attempt),
                        max_delay
                    )
                    
                    if jitter:
                        delay *= (0.5 + random.random() / 2)
                    
                    logger.warning(
                        f"Retrying {func.__name__} after {delay:.2f}s "
                        f"(attempt {attempt + 1}/{max_retries + 1}) "
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
```

## Usage Examples

### Operation Execution
```python
from s3tester.operations.registry import OperationRegistry
from s3tester.operations.base import OperationContext
import boto3

# Create S3 client
s3_client = boto3.client('s3')

# Get operation instance
operation = OperationRegistry.get_operation("PutObject")

# Create execution context
context = OperationContext(
    s3_client=s3_client,
    operation_name="PutObject",
    parameters={
        'bucket': 'test-bucket',
        'key': 'test-object',
        'body': 'file://./test-data.txt'
    },
    config_dir=Path('/path/to/config')
)

# Execute operation
result = operation.execute(context)
print(f"Success: {result.success}, Duration: {result.duration}s")
```

### Adding New Operations
```python
from s3tester.operations.base import S3Operation
from s3tester.operations.registry import OperationRegistry

class CustomOperation(S3Operation):
    def __init__(self):
        super().__init__("CustomOperation")
    
    def validate_parameters(self, parameters):
        # Validation logic
        return parameters
    
    def execute_operation(self, context):
        # Implementation logic
        pass

# Register new operation
OperationRegistry.register("CustomOperation", CustomOperation)
```

## Implementation Notes

1. **Error Classification**: Operations distinguish between retryable and non-retryable errors
2. **Parameter Validation**: Each operation validates its specific parameter requirements
3. **File Handling**: File references are resolved relative to configuration directory
4. **Dry Run Support**: All operations support dry run mode for validation
5. **Extensibility**: Registry pattern allows easy addition of new operations
6. **Logging**: Comprehensive logging for debugging and monitoring
7. **Performance**: Efficient parameter transformation with minimal overhead

## Next Steps

These operation implementations provide:
1. **Foundation for Core Engine**: Ready for integration with execution orchestration
2. **Test Implementation**: Contract tests can validate each operation independently  
3. **CLI Integration**: Operations can be invoked through command-line interface
4. **Error Reporting**: Consistent error handling for user feedback
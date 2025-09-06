"""Object operations for S3 testing.

This module implements S3 object-related operations including:
- PutObject
- GetObject
- DeleteObject
- HeadObject
"""

from typing import Dict, Any, Union
from pathlib import Path
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
                # config_dir가 없을 경우에만 cwd() 사용
                config_dir = parameters.get('_config_dir')
                if config_dir is None:
                    import logging
                    logger = logging.getLogger("s3tester.operation")
                    logger.warning("No _config_dir provided for file reference, using current working directory")
                    config_dir = Path.cwd()
                    
                # 디버깅 로그 추가
                import logging
                logger = logging.getLogger("s3tester.operation")
                logger.debug(f"Using config_dir: {config_dir} for file reference: {parameters['body']}")
                
                validated['Body'] = ParameterTransformer.transform_file_reference(
                    parameters['body'], 
                    config_dir
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
            error_message = e.response['Error']['Message']
            self.logger.error(f"PutObject failed: {error_code} - {error_message}")
            
            # Handle expected errors
            if error_code in ['NoSuchBucket', 'AccessDenied', 'InvalidBucketName']:
                return OperationResult(
                    success=False,
                    duration=0.0,
                    error_code=error_code,
                    error_message=error_message,
                    response=e.response
                )
            
            # Pass through any other client errors as failures instead of raising
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


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
            error_message = e.response['Error']['Message']
            self.logger.error(f"GetObject failed: {error_code} - {error_message}")
            
            # Handle all client errors as failures with proper information
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


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
            error_message = e.response['Error']['Message']
            self.logger.error(f"DeleteObject failed: {error_code} - {error_message}")
            
            # Handle all client errors as failures with proper information
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


class HeadObjectOperation(S3Operation):
    """Check object existence and metadata."""
    
    def __init__(self):
        super().__init__("HeadObject")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate HeadObject parameters."""
        required_params = ['bucket', 'key']
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"HeadObject requires '{param}' parameter")
        
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
        """Execute HeadObject operation."""
        try:
            response = context.s3_client.head_object(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"HeadObject failed: {error_code} - {error_message}")
            
            # Handle all client errors as failures with proper information
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )

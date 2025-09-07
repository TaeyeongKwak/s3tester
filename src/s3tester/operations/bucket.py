"""Bucket operations for S3 testing.

This module implements S3 bucket-related operations including:
- CreateBucket
- DeleteBucket
- ListBuckets
- HeadBucket
"""

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
            error_message = e.response['Error']['Message']
            self.logger.error(f"CreateBucket failed: {error_code} - {error_message}")
            
            # Handle all client errors as failures with proper information
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


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
            error_message = e.response['Error']['Message']
            self.logger.error(f"DeleteBucket failed: {error_code} - {error_message}")
            
            # Handle all client errors as failures with proper information
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


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


class HeadBucketOperation(S3Operation):
    """Check bucket existence and permissions."""
    
    def __init__(self):
        super().__init__("HeadBucket")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate HeadBucket parameters."""
        if 'bucket' not in parameters:
            raise ValueError("HeadBucket requires 'bucket' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        return {'Bucket': bucket}
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute HeadBucket operation."""
        try:
            response = context.s3_client.head_bucket(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"HeadBucket failed: {error_code} - {error_message}")
            
            # Handle all client errors as failures with proper information
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )

"""Extended object operations for S3 testing.

This module implements additional S3 object-related operations including:
- CopyObject
- GetObjectTagging
- PutObjectTagging
- DeleteObjectTagging
"""

from typing import Dict, Any
from botocore.exceptions import ClientError
from .base import S3Operation, OperationContext, OperationResult
from .parameters import ParameterTransformer


class CopyObjectOperation(S3Operation):
    """Copy an object within S3."""
    
    def __init__(self):
        super().__init__("CopyObject")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate CopyObject parameters."""
        required_params = ['source_bucket', 'source_key', 'bucket', 'key']
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"CopyObject requires '{param}' parameter")
        
        # Validate bucket and key names
        source_bucket = ParameterTransformer.transform_bucket_name(parameters['source_bucket'])
        source_key = ParameterTransformer.transform_object_key(parameters['source_key'])
        dest_bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        dest_key = ParameterTransformer.transform_object_key(parameters['key'])
        
        # Construct copy source string
        copy_source = {
            'Bucket': source_bucket,
            'Key': source_key
        }
        
        # Add version ID if specified
        if 'version_id' in parameters:
            copy_source['VersionId'] = parameters['version_id']
        
        validated = {
            'Bucket': dest_bucket,
            'Key': dest_key,
            'CopySource': copy_source
        }
        
        # Handle optional parameters
        optional_params = {
            'metadata_directive': 'MetadataDirective',
            'tagging_directive': 'TaggingDirective',
            'server_side_encryption': 'ServerSideEncryption',
            'storage_class': 'StorageClass',
            'content_type': 'ContentType',
            'cache_control': 'CacheControl',
            'content_disposition': 'ContentDisposition',
            'content_encoding': 'ContentEncoding',
            'content_language': 'ContentLanguage',
            'expires': 'Expires',
            'acl': 'ACL',
        }
        
        for src_param, dest_param in optional_params.items():
            if src_param in parameters:
                validated[dest_param] = parameters[src_param]
        
        # Handle metadata if provided
        if 'metadata' in parameters:
            if isinstance(parameters['metadata'], dict):
                validated['Metadata'] = parameters['metadata']
            else:
                raise ValueError("Metadata must be a dictionary")
        
        # Handle tagging
        if 'tags' in parameters:
            validated['Tagging'] = ParameterTransformer.transform_tagging(parameters['tags'])
            
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute CopyObject operation."""
        try:
            # The CopySource needs to be formatted as string for the API
            if isinstance(context.parameters['CopySource'], dict):
                source_dict = context.parameters['CopySource']
                
                # Path-style URL 형식을 사용
                if context.s3_client.meta.config.s3.get('addressing_style') == 'path':
                    source_str = f"{source_dict['Bucket']}/{source_dict['Key']}"
                else:
                    # Virtual-hosted style URL을 사용
                    source_str = f"{source_dict['Bucket']}/{source_dict['Key']}"
                
                if 'VersionId' in source_dict:
                    source_str += f"?versionId={source_dict['VersionId']}"
                    
                context.parameters['CopySource'] = source_str
            
            response = context.s3_client.copy_object(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"CopyObject failed: {error_code} - {error_message}")
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


class GetObjectTaggingOperation(S3Operation):
    """Get the tags for an S3 object."""
    
    def __init__(self):
        super().__init__("GetObjectTagging")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GetObjectTagging parameters."""
        required_params = ['bucket', 'key']
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"GetObjectTagging requires '{param}' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        key = ParameterTransformer.transform_object_key(parameters['key'])
        
        validated = {
            'Bucket': bucket,
            'Key': key
        }
        
        # Add version ID if specified
        if 'version_id' in parameters:
            validated['VersionId'] = parameters['version_id']
            
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute GetObjectTagging operation."""
        try:
            response = context.s3_client.get_object_tagging(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"GetObjectTagging failed: {error_code} - {error_message}")
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


class PutObjectTaggingOperation(S3Operation):
    """Set the tags for an S3 object."""
    
    def __init__(self):
        super().__init__("PutObjectTagging")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PutObjectTagging parameters."""
        required_params = ['bucket', 'key', 'tags']
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"PutObjectTagging requires '{param}' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        key = ParameterTransformer.transform_object_key(parameters['key'])
        tags = parameters['tags']
        
        if not isinstance(tags, dict):
            raise ValueError("Tags must be provided as a dictionary")
        
        tag_set = [{'Key': k, 'Value': str(v)} for k, v in tags.items()]
        
        validated = {
            'Bucket': bucket,
            'Key': key,
            'Tagging': {
                'TagSet': tag_set
            }
        }
        
        # Add version ID if specified
        if 'version_id' in parameters:
            validated['VersionId'] = parameters['version_id']
            
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute PutObjectTagging operation."""
        try:
            response = context.s3_client.put_object_tagging(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"PutObjectTagging failed: {error_code} - {error_message}")
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


class DeleteObjectTaggingOperation(S3Operation):
    """Remove all tags from an S3 object."""
    
    def __init__(self):
        super().__init__("DeleteObjectTagging")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate DeleteObjectTagging parameters."""
        required_params = ['bucket', 'key']
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"DeleteObjectTagging requires '{param}' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        key = ParameterTransformer.transform_object_key(parameters['key'])
        
        validated = {
            'Bucket': bucket,
            'Key': key
        }
        
        # Add version ID if specified
        if 'version_id' in parameters:
            validated['VersionId'] = parameters['version_id']
            
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute DeleteObjectTagging operation."""
        try:
            response = context.s3_client.delete_object_tagging(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"DeleteObjectTagging failed: {error_code} - {error_message}")
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )

"""Extended bucket operations for S3 testing.

This module implements extended S3 bucket-related operations including:
- ListObjectsV2
- ListObjectVersions
- GetBucketLocation
- GetBucketVersioning
- PutBucketVersioning
- GetBucketTagging
- PutBucketTagging
- DeleteBucketTagging
"""

from typing import Dict, Any
from botocore.exceptions import ClientError
from .base import S3Operation, OperationContext, OperationResult
from .parameters import ParameterTransformer


class ListObjectsV2Operation(S3Operation):
    """List objects in an S3 bucket using V2 API."""
    
    def __init__(self):
        super().__init__("ListObjectsV2")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ListObjectsV2 parameters."""
        if 'bucket' not in parameters:
            raise ValueError("ListObjectsV2 requires 'bucket' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        
        validated = {'Bucket': bucket}
        
        # Handle optional parameters
        if 'prefix' in parameters:
            validated['Prefix'] = parameters['prefix']
            
        if 'delimiter' in parameters:
            validated['Delimiter'] = parameters['delimiter']
            
        if 'max_keys' in parameters:
            validated['MaxKeys'] = parameters['max_keys']
            
        if 'start_after' in parameters:
            validated['StartAfter'] = parameters['start_after']
            
        if 'continuation_token' in parameters:
            validated['ContinuationToken'] = parameters['continuation_token']
        
        if 'fetch_owner' in parameters:
            validated['FetchOwner'] = parameters['fetch_owner']
            
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute ListObjectsV2 operation."""
        try:
            response = context.s3_client.list_objects_v2(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,  # Will be set by base class
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"ListObjectsV2 failed: {error_code} - {error_message}")
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


class ListObjectVersionsOperation(S3Operation):
    """List all versions of objects in an S3 bucket."""
    
    def __init__(self):
        super().__init__("ListObjectVersions")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ListObjectVersions parameters."""
        if 'bucket' not in parameters:
            raise ValueError("ListObjectVersions requires 'bucket' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        
        validated = {'Bucket': bucket}
        
        # Handle optional parameters
        if 'prefix' in parameters:
            validated['Prefix'] = parameters['prefix']
            
        if 'delimiter' in parameters:
            validated['Delimiter'] = parameters['delimiter']
            
        if 'max_keys' in parameters:
            validated['MaxKeys'] = parameters['max_keys']
            
        if 'key_marker' in parameters:
            validated['KeyMarker'] = parameters['key_marker']
            
        if 'version_id_marker' in parameters:
            validated['VersionIdMarker'] = parameters['version_id_marker']
            
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute ListObjectVersions operation."""
        try:
            response = context.s3_client.list_object_versions(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"ListObjectVersions failed: {error_code} - {error_message}")
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


class GetBucketLocationOperation(S3Operation):
    """Get the location (region) of an S3 bucket."""
    
    def __init__(self):
        super().__init__("GetBucketLocation")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GetBucketLocation parameters."""
        if 'bucket' not in parameters:
            raise ValueError("GetBucketLocation requires 'bucket' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        return {'Bucket': bucket}
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute GetBucketLocation operation."""
        try:
            response = context.s3_client.get_bucket_location(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"GetBucketLocation failed: {error_code} - {error_message}")
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


class GetBucketVersioningOperation(S3Operation):
    """Get the versioning configuration of an S3 bucket."""
    
    def __init__(self):
        super().__init__("GetBucketVersioning")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GetBucketVersioning parameters."""
        if 'bucket' not in parameters:
            raise ValueError("GetBucketVersioning requires 'bucket' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        return {'Bucket': bucket}
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute GetBucketVersioning operation."""
        try:
            response = context.s3_client.get_bucket_versioning(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"GetBucketVersioning failed: {error_code} - {error_message}")
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


class PutBucketVersioningOperation(S3Operation):
    """Set the versioning configuration of an S3 bucket."""
    
    def __init__(self):
        super().__init__("PutBucketVersioning")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PutBucketVersioning parameters."""
        if 'bucket' not in parameters:
            raise ValueError("PutBucketVersioning requires 'bucket' parameter")
            
        if 'status' not in parameters:
            raise ValueError("PutBucketVersioning requires 'status' parameter")
            
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        status = parameters['status']
        
        # Validate status value
        if status not in ['Enabled', 'Suspended']:
            raise ValueError("Versioning status must be either 'Enabled' or 'Suspended'")
            
        validated = {
            'Bucket': bucket,
            'VersioningConfiguration': {
                'Status': status
            }
        }
        
        # Add MFA Delete if specified
        if 'mfa_delete' in parameters:
            if parameters['mfa_delete'] not in ['Enabled', 'Disabled']:
                raise ValueError("MFA Delete must be either 'Enabled' or 'Disabled'")
            
            validated['VersioningConfiguration']['MFADelete'] = parameters['mfa_delete']
            
        # Add MFA if specified and required
        if 'mfa' in parameters:
            validated['MFA'] = parameters['mfa']
            
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute PutBucketVersioning operation."""
        try:
            response = context.s3_client.put_bucket_versioning(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"PutBucketVersioning failed: {error_code} - {error_message}")
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


class GetBucketTaggingOperation(S3Operation):
    """Get the tag set for an S3 bucket."""
    
    def __init__(self):
        super().__init__("GetBucketTagging")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GetBucketTagging parameters."""
        if 'bucket' not in parameters:
            raise ValueError("GetBucketTagging requires 'bucket' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        return {'Bucket': bucket}
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute GetBucketTagging operation."""
        try:
            response = context.s3_client.get_bucket_tagging(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"GetBucketTagging failed: {error_code} - {error_message}")
            
            # NoSuchTagSet is common when no tags exist
            if error_code == 'NoSuchTagSet':
                return OperationResult(
                    success=True,
                    duration=0.0,
                    response={'TagSet': []}
                )
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


class PutBucketTaggingOperation(S3Operation):
    """Set the tag set for an S3 bucket."""
    
    def __init__(self):
        super().__init__("PutBucketTagging")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PutBucketTagging parameters."""
        if 'bucket' not in parameters:
            raise ValueError("PutBucketTagging requires 'bucket' parameter")
            
        if 'tags' not in parameters:
            raise ValueError("PutBucketTagging requires 'tags' parameter")
            
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        tags = parameters['tags']
        
        if not isinstance(tags, dict):
            raise ValueError("Tags must be provided as a dictionary")
        
        tag_set = [{'Key': k, 'Value': str(v)} for k, v in tags.items()]
        
        return {
            'Bucket': bucket,
            'Tagging': {
                'TagSet': tag_set
            }
        }
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute PutBucketTagging operation."""
        try:
            response = context.s3_client.put_bucket_tagging(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"PutBucketTagging failed: {error_code} - {error_message}")
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


class DeleteBucketTaggingOperation(S3Operation):
    """Remove all tags from an S3 bucket."""
    
    def __init__(self):
        super().__init__("DeleteBucketTagging")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate DeleteBucketTagging parameters."""
        if 'bucket' not in parameters:
            raise ValueError("DeleteBucketTagging requires 'bucket' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        return {'Bucket': bucket}
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute DeleteBucketTagging operation."""
        try:
            response = context.s3_client.delete_bucket_tagging(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"DeleteBucketTagging failed: {error_code} - {error_message}")
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )

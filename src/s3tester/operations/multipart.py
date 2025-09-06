"""Multipart upload operations for S3 testing.

This module implements S3 multipart upload operations including:
- CreateMultipartUpload
- UploadPart
- CompleteMultipartUpload
- AbortMultipartUpload
- ListParts
"""

from typing import Dict, Any, List
from pathlib import Path
from botocore.exceptions import ClientError
from .base import S3Operation, OperationContext, OperationResult
from .parameters import ParameterTransformer
from ..config.models import FileReference


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
                config_dir = parameters.get('_config_dir', Path.cwd())
                validated['Body'] = ParameterTransformer.transform_file_reference(
                    parameters['body'],
                    config_dir
                )
            else:
                validated['Body'] = parameters['body']
        else:
            raise ValueError("UploadPart requires 'body' parameter")
        
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


class CompleteMultipartUploadOperation(S3Operation):
    """Complete multipart upload operation."""
    
    def __init__(self):
        super().__init__("CompleteMultipartUpload")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate CompleteMultipartUpload parameters."""
        required_params = ['bucket', 'key', 'upload_id', 'parts']
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"CompleteMultipartUpload requires '{param}' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        key = ParameterTransformer.transform_object_key(parameters['key'])
        
        # Validate parts
        parts = parameters['parts']
        if not isinstance(parts, list) or not parts:
            raise ValueError("Parts must be a non-empty list")
            
        # Ensure parts are properly formatted
        formatted_parts = []
        for part in parts:
            if not isinstance(part, dict):
                raise ValueError("Each part must be a dictionary")
            
            if 'ETag' not in part or 'PartNumber' not in part:
                raise ValueError("Each part must contain ETag and PartNumber")
            
            formatted_parts.append({
                'ETag': part['ETag'],
                'PartNumber': int(part['PartNumber'])
            })
        
        validated = {
            'Bucket': bucket,
            'Key': key,
            'UploadId': parameters['upload_id'],
            'MultipartUpload': {
                'Parts': formatted_parts
            }
        }
        
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute CompleteMultipartUpload operation."""
        try:
            response = context.s3_client.complete_multipart_upload(**context.parameters)
            
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


class AbortMultipartUploadOperation(S3Operation):
    """Abort multipart upload operation."""
    
    def __init__(self):
        super().__init__("AbortMultipartUpload")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate AbortMultipartUpload parameters."""
        required_params = ['bucket', 'key', 'upload_id']
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"AbortMultipartUpload requires '{param}' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        key = ParameterTransformer.transform_object_key(parameters['key'])
        
        validated = {
            'Bucket': bucket,
            'Key': key,
            'UploadId': parameters['upload_id']
        }
        
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute AbortMultipartUpload operation."""
        try:
            response = context.s3_client.abort_multipart_upload(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code in ['NoSuchUpload']:
                return OperationResult(
                    success=False,
                    duration=0.0,
                    error_code=error_code,
                    error_message=e.response['Error']['Message'],
                    response=e.response
                )
            
            raise


class ListPartsOperation(S3Operation):
    """List parts for multipart upload operation."""
    
    def __init__(self):
        super().__init__("ListParts")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ListParts parameters."""
        required_params = ['bucket', 'key', 'upload_id']
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"ListParts requires '{param}' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        key = ParameterTransformer.transform_object_key(parameters['key'])
        
        validated = {
            'Bucket': bucket,
            'Key': key,
            'UploadId': parameters['upload_id']
        }
        
        # Optional parameters
        if 'max_parts' in parameters:
            validated['MaxParts'] = int(parameters['max_parts'])
            
        if 'part_number_marker' in parameters:
            validated['PartNumberMarker'] = int(parameters['part_number_marker'])
        
        return validated
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute ListParts operation."""
        try:
            response = context.s3_client.list_parts(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code in ['NoSuchUpload', 'NoSuchBucket']:
                return OperationResult(
                    success=False,
                    duration=0.0,
                    error_code=error_code,
                    error_message=e.response['Error']['Message'],
                    response=e.response
                )
            
            raise

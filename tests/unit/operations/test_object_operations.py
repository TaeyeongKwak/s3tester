"""Unit tests for S3 object operations."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

from s3tester.operations.object import (
    PutObjectOperation,
    GetObjectOperation, 
    DeleteObjectOperation,
    HeadObjectOperation
)
from s3tester.operations.base import OperationContext, OperationResult
from s3tester.config.models import FileReference
from .conftest import create_client_error


class TestPutObjectOperation:
    """Test cases for PutObjectOperation."""
    
    def test_put_object_init(self):
        """Test PutObjectOperation initialization."""
        operation = PutObjectOperation()
        assert operation.operation_name == "PutObject"
    
    # Parameter validation tests
    def test_put_object_missing_bucket(self):
        """Test validation fails when bucket parameter is missing."""
        operation = PutObjectOperation()
        parameters = {'key': 'test-key'}
        
        with pytest.raises(ValueError, match="PutObject requires 'bucket' parameter"):
            operation.validate_parameters(parameters)
    
    def test_put_object_missing_key(self):
        """Test validation fails when key parameter is missing."""
        operation = PutObjectOperation()
        parameters = {'bucket': 'test-bucket'}
        
        with pytest.raises(ValueError, match="PutObject requires 'key' parameter"):
            operation.validate_parameters(parameters)
    
    def test_put_object_valid_minimal_params(self):
        """Test validation succeeds with minimal required parameters."""
        operation = PutObjectOperation()
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key'
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == 'test-bucket'
        assert result['Key'] == 'test-key'
        assert 'Body' not in result  # No body provided
    
    def test_put_object_string_body(self):
        """Test validation with string body content."""
        operation = PutObjectOperation()
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key',
            'body': 'Hello, World!'
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == 'test-bucket'
        assert result['Key'] == 'test-key'
        assert result['Body'] == b'Hello, World!'
    
    def test_put_object_file_url_body(self, temp_config_dir, sample_text_file):
        """Test validation with file:// URL body."""
        operation = PutObjectOperation()
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key',
            'body': f'file://{sample_text_file.name}',
            '_config_dir': temp_config_dir
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == 'test-bucket'
        assert result['Key'] == 'test-key'
        assert result['Body'] == b'Hello, World!'
    
    def test_put_object_file_reference_body(self, temp_config_dir, sample_text_file):
        """Test validation with FileReference object body."""
        operation = PutObjectOperation()
        file_ref = FileReference.from_path_spec(str(sample_text_file), temp_config_dir)
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key',
            'body': file_ref,
            '_config_dir': temp_config_dir
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == 'test-bucket'
        assert result['Key'] == 'test-key'
        assert result['Body'] == b'Hello, World!'
    
    def test_put_object_file_not_found(self, temp_config_dir):
        """Test validation fails when referenced file does not exist."""
        operation = PutObjectOperation()
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key',
            'body': 'file://nonexistent.txt',
            '_config_dir': temp_config_dir
        }
        
        with pytest.raises(FileNotFoundError):
            operation.validate_parameters(parameters)
    
    def test_put_object_with_metadata(self):
        """Test validation with metadata parameter."""
        operation = PutObjectOperation()
        metadata = {'author': 'test', 'version': '1.0'}
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key',
            'metadata': metadata
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Metadata'] == metadata
    
    def test_put_object_with_content_type(self):
        """Test validation with content_type parameter."""
        operation = PutObjectOperation()
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key',
            'content_type': 'application/json'
        }
        
        result = operation.validate_parameters(parameters)
        assert result['ContentType'] == 'application/json'
    
    def test_put_object_with_tags(self):
        """Test validation with tags parameter."""
        operation = PutObjectOperation()
        tags = {'Environment': 'test', 'Owner': 'developer'}
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key',
            'tags': tags
        }
        
        result = operation.validate_parameters(parameters)
        assert 'Tagging' in result
        # Tags should be converted to URL-encoded string format
        assert 'Environment=test&Owner=developer' in result['Tagging'] or 'Owner=developer&Environment=test' in result['Tagging']
    
    # Execution tests
    def test_put_object_success(self, operation_context_factory, mock_s3_client):
        """Test successful PutObject execution."""
        operation = PutObjectOperation()
        context = operation_context_factory(
            'PutObject',
            {
                'Bucket': 'test-bucket',
                'Key': 'test-key',
                'Body': b'Hello, World!'
            }
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert result.response is not None
        assert 'ETag' in result.response
        mock_s3_client.put_object.assert_called_once()
    
    def test_put_object_success_with_all_params(self, operation_context_factory, mock_s3_client):
        """Test successful PutObject with all parameters."""
        operation = PutObjectOperation()
        context = operation_context_factory(
            'PutObject',
            {
                'Bucket': 'test-bucket',
                'Key': 'test-key',
                'Body': b'Hello, World!',
                'ContentType': 'text/plain',
                'Metadata': {'author': 'test'},
                'Tagging': 'Environment=test'
            }
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert result.response is not None
        mock_s3_client.put_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test-key',
            Body=b'Hello, World!',
            ContentType='text/plain',
            Metadata={'author': 'test'},
            Tagging='Environment=test'
        )
    
    def test_put_object_no_such_bucket(self, operation_context_factory, mock_s3_client):
        """Test PutObject with NoSuchBucket error."""
        operation = PutObjectOperation()
        context = operation_context_factory('PutObject', {'Bucket': 'test-bucket', 'Key': 'test-key'})
        
        # Configure mock to raise ClientError
        mock_s3_client.put_object.side_effect = create_client_error('NoSuchBucket', 'The specified bucket does not exist', 404)
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'
        assert 'does not exist' in result.error_message
    
    def test_put_object_access_denied(self, operation_context_factory, mock_s3_client):
        """Test PutObject with AccessDenied error."""
        operation = PutObjectOperation()
        context = operation_context_factory('PutObject', {'Bucket': 'test-bucket', 'Key': 'test-key'})
        
        mock_s3_client.put_object.side_effect = create_client_error('AccessDenied', 'Access Denied', 403)
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'AccessDenied'
        assert result.error_message == 'Access Denied'
    
    def test_put_object_invalid_bucket_name(self, operation_context_factory, mock_s3_client):
        """Test PutObject with InvalidBucketName error."""
        operation = PutObjectOperation()
        context = operation_context_factory('PutObject', {'Bucket': 'invalid-bucket', 'Key': 'test-key'})
        
        mock_s3_client.put_object.side_effect = create_client_error('InvalidBucketName', 'The specified bucket is not valid', 400)
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'InvalidBucketName'
    
    def test_put_object_other_client_error(self, operation_context_factory, mock_s3_client):
        """Test PutObject with other ClientError."""
        operation = PutObjectOperation()
        context = operation_context_factory('PutObject', {'Bucket': 'test-bucket', 'Key': 'test-key'})
        
        mock_s3_client.put_object.side_effect = create_client_error('InternalError', 'We encountered an internal error', 500)
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'InternalError'
        assert result.error_message == 'We encountered an internal error'


class TestGetObjectOperation:
    """Test cases for GetObjectOperation."""
    
    def test_get_object_init(self):
        """Test GetObjectOperation initialization."""
        operation = GetObjectOperation()
        assert operation.operation_name == "GetObject"
    
    # Parameter validation tests
    def test_get_object_missing_bucket(self):
        """Test validation fails when bucket parameter is missing."""
        operation = GetObjectOperation()
        parameters = {'key': 'test-key'}
        
        with pytest.raises(ValueError, match="GetObject requires 'bucket' parameter"):
            operation.validate_parameters(parameters)
    
    def test_get_object_missing_key(self):
        """Test validation fails when key parameter is missing."""
        operation = GetObjectOperation()
        parameters = {'bucket': 'test-bucket'}
        
        with pytest.raises(ValueError, match="GetObject requires 'key' parameter"):
            operation.validate_parameters(parameters)
    
    def test_get_object_valid_minimal_params(self):
        """Test validation succeeds with minimal required parameters."""
        operation = GetObjectOperation()
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key'
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == 'test-bucket'
        assert result['Key'] == 'test-key'
    
    def test_get_object_with_version_id(self):
        """Test validation with version_id parameter."""
        operation = GetObjectOperation()
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key',
            'version_id': 'version123'
        }
        
        result = operation.validate_parameters(parameters)
        assert result['VersionId'] == 'version123'
    
    def test_get_object_with_range(self):
        """Test validation with range parameter."""
        operation = GetObjectOperation()
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key',
            'range': 'bytes=0-1023'
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Range'] == 'bytes=0-1023'
    
    # Execution tests
    def test_get_object_success(self, operation_context_factory, mock_s3_client):
        """Test successful GetObject execution."""
        operation = GetObjectOperation()
        context = operation_context_factory(
            'GetObject',
            {
                'Bucket': 'test-bucket',
                'Key': 'test-key'
            }
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert result.response is not None
        assert 'ContentLength' in result.response
        assert result.response['Body'] == b'Hello, World!'  # Body should be read
        mock_s3_client.get_object.assert_called_once()
    
    def test_get_object_body_reading(self, operation_context_factory, mock_s3_client):
        """Test that GetObject properly reads the Body stream."""
        operation = GetObjectOperation()
        context = operation_context_factory('GetObject', {'Bucket': 'test-bucket', 'Key': 'test-key'})
        
        # Create mock body that tracks read() calls
        mock_body = MagicMock()
        mock_body.read.return_value = b'Test content'
        
        mock_s3_client.get_object.return_value = {
            'Body': mock_body,
            'ContentLength': 12,
            'ResponseMetadata': {'HTTPStatusCode': 200}
        }
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert result.response['Body'] == b'Test content'
        mock_body.read.assert_called_once()
    
    def test_get_object_no_such_key(self, operation_context_factory, mock_s3_client):
        """Test GetObject with NoSuchKey error."""
        operation = GetObjectOperation()
        context = operation_context_factory('GetObject', {'Bucket': 'test-bucket', 'Key': 'nonexistent-key'})
        
        mock_s3_client.get_object.side_effect = create_client_error('NoSuchKey', 'The specified key does not exist', 404)
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'NoSuchKey'
        assert 'does not exist' in result.error_message
    
    def test_get_object_no_such_bucket(self, operation_context_factory, mock_s3_client):
        """Test GetObject with NoSuchBucket error."""
        operation = GetObjectOperation()
        context = operation_context_factory('GetObject', {'Bucket': 'nonexistent-bucket', 'Key': 'test-key'})
        
        mock_s3_client.get_object.side_effect = create_client_error('NoSuchBucket', 'The specified bucket does not exist', 404)
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'
    
    def test_get_object_access_denied(self, operation_context_factory, mock_s3_client):
        """Test GetObject with AccessDenied error."""
        operation = GetObjectOperation()
        context = operation_context_factory('GetObject', {'Bucket': 'test-bucket', 'Key': 'test-key'})
        
        mock_s3_client.get_object.side_effect = create_client_error('AccessDenied', 'Access Denied', 403)
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'AccessDenied'


class TestDeleteObjectOperation:
    """Test cases for DeleteObjectOperation."""
    
    def test_delete_object_init(self):
        """Test DeleteObjectOperation initialization."""
        operation = DeleteObjectOperation()
        assert operation.operation_name == "DeleteObject"
    
    # Parameter validation tests
    def test_delete_object_missing_bucket(self):
        """Test validation fails when bucket parameter is missing."""
        operation = DeleteObjectOperation()
        parameters = {'key': 'test-key'}
        
        with pytest.raises(ValueError, match="DeleteObject requires 'bucket' parameter"):
            operation.validate_parameters(parameters)
    
    def test_delete_object_missing_key(self):
        """Test validation fails when key parameter is missing."""
        operation = DeleteObjectOperation()
        parameters = {'bucket': 'test-bucket'}
        
        with pytest.raises(ValueError, match="DeleteObject requires 'key' parameter"):
            operation.validate_parameters(parameters)
    
    def test_delete_object_valid_params(self):
        """Test validation succeeds with valid parameters."""
        operation = DeleteObjectOperation()
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key'
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == 'test-bucket'
        assert result['Key'] == 'test-key'
    
    def test_delete_object_with_version_id(self):
        """Test validation with version_id parameter."""
        operation = DeleteObjectOperation()
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key',
            'version_id': 'version123'
        }
        
        result = operation.validate_parameters(parameters)
        assert result['VersionId'] == 'version123'
    
    # Execution tests
    def test_delete_object_success(self, operation_context_factory, mock_s3_client):
        """Test successful DeleteObject execution."""
        operation = DeleteObjectOperation()
        context = operation_context_factory(
            'DeleteObject',
            {
                'Bucket': 'test-bucket',
                'Key': 'test-key'
            }
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert result.response is not None
        mock_s3_client.delete_object.assert_called_once()
    
    def test_delete_object_nonexistent_key(self, operation_context_factory, mock_s3_client):
        """Test DeleteObject with nonexistent key (should still succeed in S3)."""
        operation = DeleteObjectOperation()
        context = operation_context_factory('DeleteObject', {'Bucket': 'test-bucket', 'Key': 'nonexistent-key'})
        
        # S3 returns success even for nonexistent keys
        mock_s3_client.delete_object.return_value = {
            'ResponseMetadata': {'HTTPStatusCode': 204}
        }
        
        result = operation.execute_operation(context)
        
        assert result.success is True
    
    def test_delete_object_no_such_bucket(self, operation_context_factory, mock_s3_client):
        """Test DeleteObject with NoSuchBucket error."""
        operation = DeleteObjectOperation()
        context = operation_context_factory('DeleteObject', {'Bucket': 'nonexistent-bucket', 'Key': 'test-key'})
        
        mock_s3_client.delete_object.side_effect = create_client_error('NoSuchBucket', 'The specified bucket does not exist', 404)
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'
    
    def test_delete_object_access_denied(self, operation_context_factory, mock_s3_client):
        """Test DeleteObject with AccessDenied error."""
        operation = DeleteObjectOperation()
        context = operation_context_factory('DeleteObject', {'Bucket': 'test-bucket', 'Key': 'test-key'})
        
        mock_s3_client.delete_object.side_effect = create_client_error('AccessDenied', 'Access Denied', 403)
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'AccessDenied'


class TestHeadObjectOperation:
    """Test cases for HeadObjectOperation."""
    
    def test_head_object_init(self):
        """Test HeadObjectOperation initialization."""
        operation = HeadObjectOperation()
        assert operation.operation_name == "HeadObject"
    
    # Parameter validation tests
    def test_head_object_missing_bucket(self):
        """Test validation fails when bucket parameter is missing."""
        operation = HeadObjectOperation()
        parameters = {'key': 'test-key'}
        
        with pytest.raises(ValueError, match="HeadObject requires 'bucket' parameter"):
            operation.validate_parameters(parameters)
    
    def test_head_object_missing_key(self):
        """Test validation fails when key parameter is missing."""
        operation = HeadObjectOperation()
        parameters = {'bucket': 'test-bucket'}
        
        with pytest.raises(ValueError, match="HeadObject requires 'key' parameter"):
            operation.validate_parameters(parameters)
    
    def test_head_object_valid_params(self):
        """Test validation succeeds with valid parameters."""
        operation = HeadObjectOperation()
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key'
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == 'test-bucket'
        assert result['Key'] == 'test-key'
    
    def test_head_object_with_version_id(self):
        """Test validation with version_id parameter."""
        operation = HeadObjectOperation()
        parameters = {
            'bucket': 'test-bucket',
            'key': 'test-key',
            'version_id': 'version123'
        }
        
        result = operation.validate_parameters(parameters)
        assert result['VersionId'] == 'version123'
    
    # Execution tests
    def test_head_object_success(self, operation_context_factory, mock_s3_client):
        """Test successful HeadObject execution."""
        operation = HeadObjectOperation()
        context = operation_context_factory(
            'HeadObject',
            {
                'Bucket': 'test-bucket',
                'Key': 'test-key'
            }
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert result.response is not None
        assert 'ContentLength' in result.response
        assert 'ETag' in result.response
        mock_s3_client.head_object.assert_called_once()
    
    def test_head_object_no_such_key(self, operation_context_factory, mock_s3_client):
        """Test HeadObject with NoSuchKey error (404 NotFound)."""
        operation = HeadObjectOperation()
        context = operation_context_factory('HeadObject', {'Bucket': 'test-bucket', 'Key': 'nonexistent-key'})
        
        mock_s3_client.head_object.side_effect = create_client_error('NoSuchKey', 'The specified key does not exist', 404)
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'NoSuchKey'
    
    def test_head_object_no_such_bucket(self, operation_context_factory, mock_s3_client):
        """Test HeadObject with NoSuchBucket error."""
        operation = HeadObjectOperation()
        context = operation_context_factory('HeadObject', {'Bucket': 'nonexistent-bucket', 'Key': 'test-key'})
        
        mock_s3_client.head_object.side_effect = create_client_error('NoSuchBucket', 'The specified bucket does not exist', 404)
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'
    
    def test_head_object_access_denied(self, operation_context_factory, mock_s3_client):
        """Test HeadObject with AccessDenied error."""
        operation = HeadObjectOperation()
        context = operation_context_factory('HeadObject', {'Bucket': 'test-bucket', 'Key': 'test-key'})
        
        mock_s3_client.head_object.side_effect = create_client_error('AccessDenied', 'Access Denied', 403)
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'AccessDenied'
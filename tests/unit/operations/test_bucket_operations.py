"""Unit tests for S3 bucket operations."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

from s3tester.operations.bucket import (
    CreateBucketOperation,
    DeleteBucketOperation,
    ListBucketsOperation,
    HeadBucketOperation
)
from s3tester.operations.base import OperationContext, OperationResult
from .conftest import create_client_error


class TestCreateBucketOperation:
    """Test cases for CreateBucketOperation."""
    
    def test_create_bucket_init(self):
        """Test CreateBucketOperation initialization."""
        operation = CreateBucketOperation()
        assert operation.operation_name == "CreateBucket"
    
    # Parameter validation tests
    def test_create_bucket_missing_bucket(self):
        """Test validation fails when bucket parameter is missing."""
        operation = CreateBucketOperation()
        parameters = {}
        
        with pytest.raises(ValueError, match="CreateBucket requires 'bucket' parameter"):
            operation.validate_parameters(parameters)
    
    def test_create_bucket_valid_minimal_params(self, valid_bucket_names):
        """Test validation succeeds with minimal required parameters."""
        operation = CreateBucketOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {'bucket': bucket_name}
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
        assert 'CreateBucketConfiguration' not in result  # No region constraint for us-east-1
        assert 'ACL' not in result
    
    def test_create_bucket_with_region_us_east_1(self, valid_bucket_names):
        """Test validation with us-east-1 region (no LocationConstraint needed)."""
        operation = CreateBucketOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {
            'bucket': bucket_name,
            'region': 'us-east-1'
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
        assert 'CreateBucketConfiguration' not in result
    
    def test_create_bucket_with_other_region(self, valid_bucket_names, aws_regions):
        """Test validation with non-us-east-1 region (LocationConstraint required)."""
        operation = CreateBucketOperation()
        bucket_name = valid_bucket_names[0]
        region = aws_regions[1]  # us-west-2
        parameters = {
            'bucket': bucket_name,
            'region': region
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
        assert 'CreateBucketConfiguration' in result
        assert result['CreateBucketConfiguration']['LocationConstraint'] == region
    
    def test_create_bucket_with_region_none(self, valid_bucket_names):
        """Test validation when region is None."""
        operation = CreateBucketOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {
            'bucket': bucket_name,
            'region': None
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
        # When region is None, it's != 'us-east-1' so CreateBucketConfiguration is added
        assert 'CreateBucketConfiguration' in result
        assert result['CreateBucketConfiguration']['LocationConstraint'] is None
    
    def test_create_bucket_with_acl(self, valid_bucket_names, s3_acl_options):
        """Test validation with ACL parameter."""
        operation = CreateBucketOperation()
        bucket_name = valid_bucket_names[0]
        acl = s3_acl_options[0]  # 'private'
        parameters = {
            'bucket': bucket_name,
            'acl': acl
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
        assert result['ACL'] == acl
    
    def test_create_bucket_with_all_params(self, valid_bucket_names, aws_regions, s3_acl_options):
        """Test validation with all parameters."""
        operation = CreateBucketOperation()
        bucket_name = valid_bucket_names[0]
        region = aws_regions[2]  # eu-west-1
        acl = s3_acl_options[1]  # 'public-read'
        parameters = {
            'bucket': bucket_name,
            'region': region,
            'acl': acl
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
        assert result['CreateBucketConfiguration']['LocationConstraint'] == region
        assert result['ACL'] == acl
    
    def test_create_bucket_name_transformation(self, valid_bucket_names):
        """Test bucket name transformation and validation."""
        operation = CreateBucketOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {'bucket': bucket_name}
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
    
    # Execution tests
    def test_create_bucket_success(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test successful CreateBucket execution."""
        operation = CreateBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory(
            'CreateBucket',
            {'Bucket': bucket_name}
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert result.response is not None
        assert 'Location' in result.response
        mock_s3_client.create_bucket.assert_called_once_with(Bucket=bucket_name)
    
    def test_create_bucket_success_with_region(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test successful CreateBucket with region execution."""
        operation = CreateBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory(
            'CreateBucket',
            {
                'Bucket': bucket_name,
                'CreateBucketConfiguration': {'LocationConstraint': 'eu-west-1'}
            }
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        mock_s3_client.create_bucket.assert_called_once_with(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'eu-west-1'}
        )
    
    def test_create_bucket_already_exists(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test CreateBucket with BucketAlreadyExists error."""
        operation = CreateBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('CreateBucket', {'Bucket': bucket_name})
        
        mock_s3_client.create_bucket.side_effect = create_client_error(
            'BucketAlreadyExists', 
            'The requested bucket name is not available', 
            409
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'BucketAlreadyExists'
        assert 'not available' in result.error_message
    
    def test_create_bucket_already_owned(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test CreateBucket with BucketAlreadyOwnedByYou error."""
        operation = CreateBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('CreateBucket', {'Bucket': bucket_name})
        
        mock_s3_client.create_bucket.side_effect = create_client_error(
            'BucketAlreadyOwnedByYou',
            'Your previous request to create the named bucket succeeded',
            409
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'BucketAlreadyOwnedByYou'
    
    def test_create_bucket_invalid_bucket_name(self, operation_context_factory, mock_s3_client):
        """Test CreateBucket with InvalidBucketName error."""
        operation = CreateBucketOperation()
        context = operation_context_factory('CreateBucket', {'Bucket': 'invalid-bucket'})
        
        mock_s3_client.create_bucket.side_effect = create_client_error(
            'InvalidBucketName',
            'The specified bucket is not valid',
            400
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'InvalidBucketName'
    
    def test_create_bucket_access_denied(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test CreateBucket with AccessDenied error."""
        operation = CreateBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('CreateBucket', {'Bucket': bucket_name})
        
        mock_s3_client.create_bucket.side_effect = create_client_error(
            'AccessDenied',
            'Access Denied',
            403
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'AccessDenied'
    
    def test_create_bucket_other_client_error(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test CreateBucket with other ClientError."""
        operation = CreateBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('CreateBucket', {'Bucket': bucket_name})
        
        mock_s3_client.create_bucket.side_effect = create_client_error(
            'InternalError',
            'We encountered an internal error',
            500
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'InternalError'


class TestDeleteBucketOperation:
    """Test cases for DeleteBucketOperation."""
    
    def test_delete_bucket_init(self):
        """Test DeleteBucketOperation initialization."""
        operation = DeleteBucketOperation()
        assert operation.operation_name == "DeleteBucket"
    
    # Parameter validation tests
    def test_delete_bucket_missing_bucket(self):
        """Test validation fails when bucket parameter is missing."""
        operation = DeleteBucketOperation()
        parameters = {}
        
        with pytest.raises(ValueError, match="DeleteBucket requires 'bucket' parameter"):
            operation.validate_parameters(parameters)
    
    def test_delete_bucket_valid_params(self, valid_bucket_names):
        """Test validation succeeds with valid parameters."""
        operation = DeleteBucketOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {'bucket': bucket_name}
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
    
    def test_delete_bucket_name_transformation(self, valid_bucket_names):
        """Test bucket name transformation."""
        operation = DeleteBucketOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {'bucket': bucket_name}
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
    
    # Execution tests
    def test_delete_bucket_success(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test successful DeleteBucket execution."""
        operation = DeleteBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory(
            'DeleteBucket',
            {'Bucket': bucket_name}
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert result.response is not None
        mock_s3_client.delete_bucket.assert_called_once_with(Bucket=bucket_name)
    
    def test_delete_bucket_no_such_bucket(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test DeleteBucket with NoSuchBucket error."""
        operation = DeleteBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('DeleteBucket', {'Bucket': bucket_name})
        
        mock_s3_client.delete_bucket.side_effect = create_client_error(
            'NoSuchBucket',
            'The specified bucket does not exist',
            404
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'
    
    def test_delete_bucket_not_empty(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test DeleteBucket with BucketNotEmpty error."""
        operation = DeleteBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('DeleteBucket', {'Bucket': bucket_name})
        
        mock_s3_client.delete_bucket.side_effect = create_client_error(
            'BucketNotEmpty',
            'The bucket you tried to delete is not empty',
            409
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'BucketNotEmpty'
    
    def test_delete_bucket_access_denied(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test DeleteBucket with AccessDenied error."""
        operation = DeleteBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('DeleteBucket', {'Bucket': bucket_name})
        
        mock_s3_client.delete_bucket.side_effect = create_client_error(
            'AccessDenied',
            'Access Denied',
            403
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'AccessDenied'
    
    def test_delete_bucket_other_client_error(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test DeleteBucket with other ClientError."""
        operation = DeleteBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('DeleteBucket', {'Bucket': bucket_name})
        
        mock_s3_client.delete_bucket.side_effect = create_client_error(
            'InternalError',
            'We encountered an internal error',
            500
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'InternalError'


class TestListBucketsOperation:
    """Test cases for ListBucketsOperation."""
    
    def test_list_buckets_init(self):
        """Test ListBucketsOperation initialization."""
        operation = ListBucketsOperation()
        assert operation.operation_name == "ListBuckets"
    
    # Parameter validation tests
    def test_list_buckets_no_params_required(self):
        """Test validation succeeds with no parameters."""
        operation = ListBucketsOperation()
        parameters = {}
        
        result = operation.validate_parameters(parameters)
        assert result == {}
    
    def test_list_buckets_empty_params(self):
        """Test validation allows empty parameters."""
        operation = ListBucketsOperation()
        parameters = {}
        
        result = operation.validate_parameters(parameters)
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_list_buckets_ignore_extra_params(self):
        """Test validation ignores extra parameters."""
        operation = ListBucketsOperation()
        parameters = {'unused_param': 'value'}
        
        result = operation.validate_parameters(parameters)
        assert result == {}
    
    # Execution tests
    def test_list_buckets_success(self, operation_context_factory, mock_s3_client):
        """Test successful ListBuckets execution."""
        operation = ListBucketsOperation()
        context = operation_context_factory('ListBuckets', {})
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert result.response is not None
        assert 'Buckets' in result.response
        assert 'Owner' in result.response
        assert len(result.response['Buckets']) == 2
        mock_s3_client.list_buckets.assert_called_once()
    
    def test_list_buckets_empty_list(self, operation_context_factory, mock_s3_client):
        """Test ListBuckets with empty bucket list."""
        operation = ListBucketsOperation()
        context = operation_context_factory('ListBuckets', {})
        
        # Configure mock to return empty list
        mock_s3_client.list_buckets.return_value = {
            'Buckets': [],
            'Owner': {'ID': 'owner-id', 'DisplayName': 'test-owner'},
            'ResponseMetadata': {'HTTPStatusCode': 200}
        }
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert result.response['Buckets'] == []
    
    def test_list_buckets_multiple_buckets(self, operation_context_factory, mock_s3_client):
        """Test ListBuckets with multiple buckets."""
        operation = ListBucketsOperation()
        context = operation_context_factory('ListBuckets', {})
        
        # Use default mock response which has 2 buckets
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert len(result.response['Buckets']) == 2
        assert result.response['Buckets'][0]['Name'] == 'bucket1'
        assert result.response['Buckets'][1]['Name'] == 'bucket2'
    
    def test_list_buckets_access_denied(self, operation_context_factory, mock_s3_client):
        """Test ListBuckets with AccessDenied error."""
        operation = ListBucketsOperation()
        context = operation_context_factory('ListBuckets', {})
        
        mock_s3_client.list_buckets.side_effect = create_client_error(
            'AccessDenied',
            'Access Denied',
            403
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'AccessDenied'
    
    def test_list_buckets_other_client_error(self, operation_context_factory, mock_s3_client):
        """Test ListBuckets with other ClientError."""
        operation = ListBucketsOperation()
        context = operation_context_factory('ListBuckets', {})
        
        mock_s3_client.list_buckets.side_effect = create_client_error(
            'ServiceUnavailable',
            'Service Unavailable',
            503
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'ServiceUnavailable'


class TestHeadBucketOperation:
    """Test cases for HeadBucketOperation."""
    
    def test_head_bucket_init(self):
        """Test HeadBucketOperation initialization."""
        operation = HeadBucketOperation()
        assert operation.operation_name == "HeadBucket"
    
    # Parameter validation tests
    def test_head_bucket_missing_bucket(self):
        """Test validation fails when bucket parameter is missing."""
        operation = HeadBucketOperation()
        parameters = {}
        
        with pytest.raises(ValueError, match="HeadBucket requires 'bucket' parameter"):
            operation.validate_parameters(parameters)
    
    def test_head_bucket_valid_params(self, valid_bucket_names):
        """Test validation succeeds with valid parameters."""
        operation = HeadBucketOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {'bucket': bucket_name}
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
    
    def test_head_bucket_name_transformation(self, valid_bucket_names):
        """Test bucket name transformation."""
        operation = HeadBucketOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {'bucket': bucket_name}
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
    
    # Execution tests
    def test_head_bucket_success(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test successful HeadBucket execution."""
        operation = HeadBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory(
            'HeadBucket',
            {'Bucket': bucket_name}
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert result.response is not None
        mock_s3_client.head_bucket.assert_called_once_with(Bucket=bucket_name)
    
    def test_head_bucket_not_found(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test HeadBucket with NotFound error (NoSuchBucket)."""
        operation = HeadBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('HeadBucket', {'Bucket': bucket_name})
        
        mock_s3_client.head_bucket.side_effect = create_client_error(
            'NoSuchBucket',
            'The specified bucket does not exist',
            404
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'
    
    def test_head_bucket_access_denied(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test HeadBucket with AccessDenied error (403 Forbidden)."""
        operation = HeadBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('HeadBucket', {'Bucket': bucket_name})
        
        mock_s3_client.head_bucket.side_effect = create_client_error(
            'AccessDenied',
            'Access Denied',
            403
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'AccessDenied'
    
    def test_head_bucket_other_client_error(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test HeadBucket with other ClientError."""
        operation = HeadBucketOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('HeadBucket', {'Bucket': bucket_name})
        
        mock_s3_client.head_bucket.side_effect = create_client_error(
            'InternalError',
            'We encountered an internal error',
            500
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'InternalError'
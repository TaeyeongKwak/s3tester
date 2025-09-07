"""Unit tests for S3 bucket policy operations."""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

from s3tester.operations.bucket_policy import (
    GetBucketPolicyOperation,
    PutBucketPolicyOperation,
    DeleteBucketPolicyOperation
)
from s3tester.operations.base import OperationContext, OperationResult
from .conftest import create_client_error


class TestGetBucketPolicyOperation:
    """Test cases for GetBucketPolicyOperation."""
    
    def test_get_bucket_policy_init(self):
        """Test GetBucketPolicyOperation initialization."""
        operation = GetBucketPolicyOperation()
        assert operation.operation_name == "GetBucketPolicy"
    
    # Parameter validation tests
    def test_get_bucket_policy_missing_bucket(self):
        """Test validation fails when bucket parameter is missing."""
        operation = GetBucketPolicyOperation()
        parameters = {}
        
        with pytest.raises(ValueError, match="GetBucketPolicy requires 'bucket' parameter"):
            operation.validate_parameters(parameters)
    
    def test_get_bucket_policy_valid_params(self, valid_bucket_names):
        """Test validation succeeds with valid parameters."""
        operation = GetBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {'bucket': bucket_name}
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
    
    def test_get_bucket_policy_name_transformation(self, valid_bucket_names):
        """Test bucket name transformation."""
        operation = GetBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {'bucket': bucket_name}
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
    
    # Execution tests
    def test_get_bucket_policy_success(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test successful GetBucketPolicy execution."""
        operation = GetBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory(
            'GetBucketPolicy',
            {'Bucket': bucket_name}
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert result.response is not None
        assert 'Policy' in result.response
        mock_s3_client.get_bucket_policy.assert_called_once_with(Bucket=bucket_name)
    
    def test_get_bucket_policy_with_json_parsing(self, operation_context_factory, mock_s3_client, valid_bucket_names, sample_bucket_policy_json):
        """Test GetBucketPolicy properly parses Policy JSON string."""
        operation = GetBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('GetBucketPolicy', {'Bucket': bucket_name})
        
        # Configure mock to return specific policy
        mock_s3_client.get_bucket_policy.return_value = {
            'Policy': sample_bucket_policy_json,
            'ResponseMetadata': {'HTTPStatusCode': 200}
        }
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert 'Policy' in result.response
        assert 'PolicyJson' in result.response
        assert isinstance(result.response['PolicyJson'], dict)
        assert result.response['PolicyJson']['Version'] == '2012-10-17'
        assert len(result.response['PolicyJson']['Statement']) == 1
    
    def test_get_bucket_policy_no_such_policy(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test GetBucketPolicy with NoSuchBucketPolicy error (treated as success)."""
        operation = GetBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('GetBucketPolicy', {'Bucket': bucket_name})
        
        mock_s3_client.get_bucket_policy.side_effect = create_client_error(
            'NoSuchBucketPolicy',
            'The bucket policy does not exist',
            404
        )
        
        result = operation.execute_operation(context)
        
        # NoSuchBucketPolicy should be treated as success
        assert result.success is True
        assert result.response['PolicyStatus'] == 'NoPolicy'
    
    def test_get_bucket_policy_no_such_bucket(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test GetBucketPolicy with NoSuchBucket error."""
        operation = GetBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('GetBucketPolicy', {'Bucket': bucket_name})
        
        mock_s3_client.get_bucket_policy.side_effect = create_client_error(
            'NoSuchBucket',
            'The specified bucket does not exist',
            404
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'
    
    def test_get_bucket_policy_access_denied(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test GetBucketPolicy with AccessDenied error."""
        operation = GetBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('GetBucketPolicy', {'Bucket': bucket_name})
        
        mock_s3_client.get_bucket_policy.side_effect = create_client_error(
            'AccessDenied',
            'Access Denied',
            403
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'AccessDenied'
    
    def test_get_bucket_policy_other_client_error(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test GetBucketPolicy with other ClientError."""
        operation = GetBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('GetBucketPolicy', {'Bucket': bucket_name})
        
        mock_s3_client.get_bucket_policy.side_effect = create_client_error(
            'InternalError',
            'We encountered an internal error',
            500
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'InternalError'


class TestPutBucketPolicyOperation:
    """Test cases for PutBucketPolicyOperation."""
    
    def test_put_bucket_policy_init(self):
        """Test PutBucketPolicyOperation initialization."""
        operation = PutBucketPolicyOperation()
        assert operation.operation_name == "PutBucketPolicy"
    
    # Parameter validation tests
    def test_put_bucket_policy_missing_bucket(self):
        """Test validation fails when bucket parameter is missing."""
        operation = PutBucketPolicyOperation()
        parameters = {'policy': '{}'}
        
        with pytest.raises(ValueError, match="PutBucketPolicy requires 'bucket' parameter"):
            operation.validate_parameters(parameters)
    
    def test_put_bucket_policy_missing_policy(self, valid_bucket_names):
        """Test validation fails when policy parameter is missing."""
        operation = PutBucketPolicyOperation()
        parameters = {'bucket': valid_bucket_names[0]}
        
        with pytest.raises(ValueError, match="PutBucketPolicy requires 'policy' parameter"):
            operation.validate_parameters(parameters)
    
    def test_put_bucket_policy_valid_params(self, valid_bucket_names, sample_bucket_policy_dict):
        """Test validation succeeds with valid parameters."""
        operation = PutBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {
            'bucket': bucket_name,
            'policy': sample_bucket_policy_dict
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
        assert 'Policy' in result
        assert isinstance(result['Policy'], str)
    
    def test_put_bucket_policy_dict_to_json(self, valid_bucket_names, sample_bucket_policy_dict):
        """Test validation converts dictionary policy to JSON string."""
        operation = PutBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {
            'bucket': bucket_name,
            'policy': sample_bucket_policy_dict
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
        
        # Policy should be converted to JSON string
        policy_json = json.loads(result['Policy'])
        assert policy_json == sample_bucket_policy_dict
    
    def test_put_bucket_policy_valid_json_string(self, valid_bucket_names, sample_bucket_policy_json):
        """Test validation accepts valid JSON string policy."""
        operation = PutBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {
            'bucket': bucket_name,
            'policy': sample_bucket_policy_json
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
        assert result['Policy'] == sample_bucket_policy_json
    
    def test_put_bucket_policy_invalid_json_string(self, valid_bucket_names):
        """Test validation fails with invalid JSON string policy."""
        operation = PutBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {
            'bucket': bucket_name,
            'policy': '{"invalid": json}'  # Invalid JSON
        }
        
        with pytest.raises(ValueError, match="Policy string must be valid JSON"):
            operation.validate_parameters(parameters)
    
    def test_put_bucket_policy_invalid_type(self, valid_bucket_names):
        """Test validation fails with invalid policy type."""
        operation = PutBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {
            'bucket': bucket_name,
            'policy': 123  # Invalid type
        }
        
        with pytest.raises(ValueError, match="Policy must be a dictionary or JSON string"):
            operation.validate_parameters(parameters)
    
    def test_put_bucket_policy_complex_dict(self, valid_bucket_names, complex_bucket_policy_dict):
        """Test validation with complex dictionary policy."""
        operation = PutBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {
            'bucket': bucket_name,
            'policy': complex_bucket_policy_dict
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
        
        # Parse back the JSON to verify complex structure is preserved
        policy_json = json.loads(result['Policy'])
        assert len(policy_json['Statement']) == 2
        assert policy_json['Statement'][0]['Sid'] == 'PublicReadGetObject'
        assert policy_json['Statement'][1]['Condition'] is not None
    
    def test_put_bucket_policy_empty_dict(self, valid_bucket_names, empty_bucket_policy_dict):
        """Test validation with empty dictionary policy."""
        operation = PutBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {
            'bucket': bucket_name,
            'policy': empty_bucket_policy_dict
        }
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
        
        # Parse back to verify empty statements
        policy_json = json.loads(result['Policy'])
        assert policy_json['Statement'] == []
    
    # Execution tests
    def test_put_bucket_policy_success(self, operation_context_factory, mock_s3_client, valid_bucket_names, sample_bucket_policy_json):
        """Test successful PutBucketPolicy execution."""
        operation = PutBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory(
            'PutBucketPolicy',
            {
                'Bucket': bucket_name,
                'Policy': sample_bucket_policy_json
            }
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert result.response is not None
        mock_s3_client.put_bucket_policy.assert_called_once_with(
            Bucket=bucket_name,
            Policy=sample_bucket_policy_json
        )
    
    def test_put_bucket_policy_success_with_dict(self, operation_context_factory, mock_s3_client, valid_bucket_names, sample_bucket_policy_dict):
        """Test successful PutBucketPolicy with dictionary policy."""
        operation = PutBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        policy_json = json.dumps(sample_bucket_policy_dict)
        context = operation_context_factory(
            'PutBucketPolicy',
            {
                'Bucket': bucket_name,
                'Policy': policy_json
            }
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        mock_s3_client.put_bucket_policy.assert_called_once_with(
            Bucket=bucket_name,
            Policy=policy_json
        )
    
    def test_put_bucket_policy_no_such_bucket(self, operation_context_factory, mock_s3_client, valid_bucket_names, sample_bucket_policy_json):
        """Test PutBucketPolicy with NoSuchBucket error."""
        operation = PutBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('PutBucketPolicy', {'Bucket': bucket_name, 'Policy': sample_bucket_policy_json})
        
        mock_s3_client.put_bucket_policy.side_effect = create_client_error(
            'NoSuchBucket',
            'The specified bucket does not exist',
            404
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'
    
    def test_put_bucket_policy_malformed_policy(self, operation_context_factory, mock_s3_client, valid_bucket_names, sample_bucket_policy_json):
        """Test PutBucketPolicy with MalformedPolicy error."""
        operation = PutBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('PutBucketPolicy', {'Bucket': bucket_name, 'Policy': sample_bucket_policy_json})
        
        mock_s3_client.put_bucket_policy.side_effect = create_client_error(
            'MalformedPolicy',
            'Policy has invalid resource',
            400
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'MalformedPolicy'
    
    def test_put_bucket_policy_access_denied(self, operation_context_factory, mock_s3_client, valid_bucket_names, sample_bucket_policy_json):
        """Test PutBucketPolicy with AccessDenied error."""
        operation = PutBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('PutBucketPolicy', {'Bucket': bucket_name, 'Policy': sample_bucket_policy_json})
        
        mock_s3_client.put_bucket_policy.side_effect = create_client_error(
            'AccessDenied',
            'Access Denied',
            403
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'AccessDenied'
    
    def test_put_bucket_policy_other_client_error(self, operation_context_factory, mock_s3_client, valid_bucket_names, sample_bucket_policy_json):
        """Test PutBucketPolicy with other ClientError."""
        operation = PutBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('PutBucketPolicy', {'Bucket': bucket_name, 'Policy': sample_bucket_policy_json})
        
        mock_s3_client.put_bucket_policy.side_effect = create_client_error(
            'InternalError',
            'We encountered an internal error',
            500
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'InternalError'


class TestDeleteBucketPolicyOperation:
    """Test cases for DeleteBucketPolicyOperation."""
    
    def test_delete_bucket_policy_init(self):
        """Test DeleteBucketPolicyOperation initialization."""
        operation = DeleteBucketPolicyOperation()
        assert operation.operation_name == "DeleteBucketPolicy"
    
    # Parameter validation tests
    def test_delete_bucket_policy_missing_bucket(self):
        """Test validation fails when bucket parameter is missing."""
        operation = DeleteBucketPolicyOperation()
        parameters = {}
        
        with pytest.raises(ValueError, match="DeleteBucketPolicy requires 'bucket' parameter"):
            operation.validate_parameters(parameters)
    
    def test_delete_bucket_policy_valid_params(self, valid_bucket_names):
        """Test validation succeeds with valid parameters."""
        operation = DeleteBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {'bucket': bucket_name}
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
    
    def test_delete_bucket_policy_name_transformation(self, valid_bucket_names):
        """Test bucket name transformation."""
        operation = DeleteBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        parameters = {'bucket': bucket_name}
        
        result = operation.validate_parameters(parameters)
        assert result['Bucket'] == bucket_name
    
    # Execution tests
    def test_delete_bucket_policy_success(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test successful DeleteBucketPolicy execution."""
        operation = DeleteBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory(
            'DeleteBucketPolicy',
            {'Bucket': bucket_name}
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is True
        assert result.response is not None
        mock_s3_client.delete_bucket_policy.assert_called_once_with(Bucket=bucket_name)
    
    def test_delete_bucket_policy_no_policy_exists(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test DeleteBucketPolicy when no policy exists (should still succeed in S3)."""
        operation = DeleteBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('DeleteBucketPolicy', {'Bucket': bucket_name})
        
        # S3 returns success even when no policy exists
        mock_s3_client.delete_bucket_policy.return_value = {
            'ResponseMetadata': {'HTTPStatusCode': 204}
        }
        
        result = operation.execute_operation(context)
        
        assert result.success is True
    
    def test_delete_bucket_policy_no_such_bucket(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test DeleteBucketPolicy with NoSuchBucket error."""
        operation = DeleteBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('DeleteBucketPolicy', {'Bucket': bucket_name})
        
        mock_s3_client.delete_bucket_policy.side_effect = create_client_error(
            'NoSuchBucket',
            'The specified bucket does not exist',
            404
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'
    
    def test_delete_bucket_policy_access_denied(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test DeleteBucketPolicy with AccessDenied error."""
        operation = DeleteBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('DeleteBucketPolicy', {'Bucket': bucket_name})
        
        mock_s3_client.delete_bucket_policy.side_effect = create_client_error(
            'AccessDenied',
            'Access Denied',
            403
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'AccessDenied'
    
    def test_delete_bucket_policy_other_client_error(self, operation_context_factory, mock_s3_client, valid_bucket_names):
        """Test DeleteBucketPolicy with other ClientError."""
        operation = DeleteBucketPolicyOperation()
        bucket_name = valid_bucket_names[0]
        context = operation_context_factory('DeleteBucketPolicy', {'Bucket': bucket_name})
        
        mock_s3_client.delete_bucket_policy.side_effect = create_client_error(
            'InternalError',
            'We encountered an internal error',
            500
        )
        
        result = operation.execute_operation(context)
        
        assert result.success is False
        assert result.error_code == 'InternalError'
"""Unit tests for bucket extended operations.

This module tests the S3 bucket extended operations including:
- ListObjectsV2Operation
- ListObjectVersionsOperation 
- GetBucketLocationOperation
- GetBucketVersioningOperation
- PutBucketVersioningOperation
- GetBucketTaggingOperation
- PutBucketTaggingOperation
- DeleteBucketTaggingOperation
"""

import pytest
from botocore.exceptions import ClientError

from s3tester.operations.bucket_extended import (
    ListObjectsV2Operation,
    ListObjectVersionsOperation,
    GetBucketLocationOperation,
    GetBucketVersioningOperation,
    PutBucketVersioningOperation,
    GetBucketTaggingOperation,
    PutBucketTaggingOperation,
    DeleteBucketTaggingOperation
)


class TestListObjectsV2Operation:
    """Test ListObjectsV2Operation class."""
    
    def test_init(self):
        """Test ListObjectsV2Operation initialization."""
        op = ListObjectsV2Operation()
        assert op.operation_name == "ListObjectsV2"
    
    def test_validate_parameters_success_basic(self):
        """Test parameter validation with basic required parameters."""
        op = ListObjectsV2Operation()
        params = {'bucket': 'test-bucket'}
        result = op.validate_parameters(params)
        assert result == {'Bucket': 'test-bucket'}
    
    def test_validate_parameters_success_all_optional(self):
        """Test parameter validation with all optional parameters."""
        op = ListObjectsV2Operation()
        params = {
            'bucket': 'test-bucket',
            'prefix': 'photos/',
            'delimiter': '/',
            'max_keys': 100,
            'start_after': 'photos/2023/',
            'continuation_token': 'token123',
            'fetch_owner': True
        }
        result = op.validate_parameters(params)
        expected = {
            'Bucket': 'test-bucket',
            'Prefix': 'photos/',
            'Delimiter': '/',
            'MaxKeys': 100,
            'StartAfter': 'photos/2023/',
            'ContinuationToken': 'token123',
            'FetchOwner': True
        }
        assert result == expected
    
    def test_validate_parameters_missing_bucket(self):
        """Test parameter validation without required bucket parameter."""
        op = ListObjectsV2Operation()
        params = {'prefix': 'photos/'}
        with pytest.raises(ValueError, match="ListObjectsV2 requires 'bucket' parameter"):
            op.validate_parameters(params)
    
    def test_execute_operation_success(self, operation_context_factory, mock_s3_client):
        """Test successful ListObjectsV2 operation execution."""
        op = ListObjectsV2Operation()
        context = operation_context_factory("ListObjectsV2", {'Bucket': 'test-bucket'})
        result = op.execute_operation(context)
        
        assert result.success is True
        assert result.error_code is None
        assert 'Contents' in result.response
        assert len(result.response['Contents']) == 2
        mock_s3_client.list_objects_v2.assert_called_once_with(Bucket='test-bucket')
    
    def test_execute_operation_with_prefix(self, operation_context_factory, mock_s3_client):
        """Test ListObjectsV2 operation with prefix parameter."""
        op = ListObjectsV2Operation()
        context = operation_context_factory("ListObjectsV2", {'Bucket': 'test-bucket', 'Prefix': 'photos/'})
        result = op.execute_operation(context)
        
        assert result.success is True
        mock_s3_client.list_objects_v2.assert_called_once_with(Bucket='test-bucket', Prefix='photos/')
    
    def test_execute_operation_client_error_no_such_bucket(self, operation_context_factory, mock_s3_client, client_error_factory):
        """Test ListObjectsV2 operation with NoSuchBucket error."""
        op = ListObjectsV2Operation()
        context = operation_context_factory("ListObjectsV2", {'Bucket': 'nonexistent-bucket'})
        
        mock_s3_client.list_objects_v2.side_effect = client_error_factory(
            'NoSuchBucket', 'The specified bucket does not exist', 404
        )
        
        result = op.execute_operation(context)
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'
        assert 'does not exist' in result.error_message
    
    def test_execute_operation_client_error_access_denied(self, operation_context_factory, mock_s3_client, client_error_factory):
        """Test ListObjectsV2 operation with AccessDenied error."""
        op = ListObjectsV2Operation()
        context = operation_context_factory("ListObjectsV2", {'Bucket': 'private-bucket'})
        
        mock_s3_client.list_objects_v2.side_effect = client_error_factory(
            'AccessDenied', 'Access Denied', 403
        )
        
        result = op.execute_operation(context)
        assert result.success is False
        assert result.error_code == 'AccessDenied'
        assert result.error_message == 'Access Denied'
    
    def test_execute_operation_empty_bucket(self, operation_context_factory, mock_s3_client):
        """Test ListObjectsV2 operation with empty bucket."""
        op = ListObjectsV2Operation()
        context = operation_context_factory("ListObjectsV2", {'Bucket': 'empty-bucket'})
        
        empty_response = {
            'Contents': [],
            'KeyCount': 0,
            'MaxKeys': 1000,
            'IsTruncated': False,
            'Name': 'empty-bucket',
            'Prefix': '',
            'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId': 'test-request-id'}
        }
        mock_s3_client.list_objects_v2.return_value = empty_response
        
        result = op.execute_operation(context)
        assert result.success is True
        assert len(result.response['Contents']) == 0
        assert result.response['KeyCount'] == 0
    
    def test_execute_operation_truncated_response(self, operation_context_factory, mock_s3_client):
        """Test ListObjectsV2 operation with truncated response."""
        op = ListObjectsV2Operation()
        context = operation_context_factory("ListObjectsV2", {'Bucket': 'large-bucket'})
        
        truncated_response = {
            'Contents': [{'Key': f'file{i}.txt'} for i in range(1000)],
            'KeyCount': 1000,
            'MaxKeys': 1000,
            'IsTruncated': True,
            'NextContinuationToken': 'next-token',
            'Name': 'large-bucket',
            'Prefix': '',
            'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId': 'test-request-id'}
        }
        mock_s3_client.list_objects_v2.return_value = truncated_response
        
        result = op.execute_operation(context)
        assert result.success is True
        assert result.response['IsTruncated'] is True
        assert 'NextContinuationToken' in result.response
    
    def test_validate_parameters_with_special_chars(self):
        """Test parameter validation with special characters in prefix."""
        op = ListObjectsV2Operation()
        params = {
            'bucket': 'test-bucket',
            'prefix': 'folder with spaces/subfolder/',
            'delimiter': '/'
        }
        result = op.validate_parameters(params)
        expected = {
            'Bucket': 'test-bucket',
            'Prefix': 'folder with spaces/subfolder/',
            'Delimiter': '/'
        }
        assert result == expected


class TestListObjectVersionsOperation:
    """Test ListObjectVersionsOperation class."""
    
    def test_init(self):
        """Test ListObjectVersionsOperation initialization."""
        op = ListObjectVersionsOperation()
        assert op.operation_name == "ListObjectVersions"
    
    def test_validate_parameters_success_basic(self):
        """Test parameter validation with basic required parameters."""
        op = ListObjectVersionsOperation()
        params = {'bucket': 'versioned-bucket'}
        result = op.validate_parameters(params)
        assert result == {'Bucket': 'versioned-bucket'}
    
    def test_validate_parameters_success_all_optional(self):
        """Test parameter validation with all optional parameters."""
        op = ListObjectVersionsOperation()
        params = {
            'bucket': 'versioned-bucket',
            'prefix': 'docs/',
            'delimiter': '/',
            'max_keys': 50,
            'key_marker': 'docs/readme.txt',
            'version_id_marker': 'version123'
        }
        result = op.validate_parameters(params)
        expected = {
            'Bucket': 'versioned-bucket',
            'Prefix': 'docs/',
            'Delimiter': '/',
            'MaxKeys': 50,
            'KeyMarker': 'docs/readme.txt',
            'VersionIdMarker': 'version123'
        }
        assert result == expected
    
    def test_validate_parameters_missing_bucket(self):
        """Test parameter validation without required bucket parameter."""
        op = ListObjectVersionsOperation()
        params = {'prefix': 'docs/'}
        with pytest.raises(ValueError, match="ListObjectVersions requires 'bucket' parameter"):
            op.validate_parameters(params)
    
    def test_execute_operation_success(self, operation_context_factory, mock_s3_client):
        """Test successful ListObjectVersions operation execution."""
        op = ListObjectVersionsOperation()
        context = operation_context_factory("ListObjectVersions", {'Bucket': 'versioned-bucket'})
        result = op.execute_operation(context)
        
        assert result.success is True
        assert 'Versions' in result.response
        assert len(result.response['Versions']) == 1
        mock_s3_client.list_object_versions.assert_called_once_with(Bucket='versioned-bucket')
    
    def test_execute_operation_client_error_no_such_bucket(self, operation_context_factory, mock_s3_client, client_error_factory):
        """Test ListObjectVersions operation with NoSuchBucket error."""
        op = ListObjectVersionsOperation()
        context = operation_context_factory("ListObjectVersions", {'Bucket': 'nonexistent-bucket'})
        
        mock_s3_client.list_object_versions.side_effect = client_error_factory(
            'NoSuchBucket', 'The specified bucket does not exist', 404
        )
        
        result = op.execute_operation(context)
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'
    
    def test_execute_operation_versioning_not_enabled(self, operation_context_factory, mock_s3_client):
        """Test ListObjectVersions operation on bucket without versioning."""
        op = ListObjectVersionsOperation()
        context = operation_context_factory("ListObjectVersions", {'Bucket': 'unversioned-bucket'})
        
        unversioned_response = {
            'Versions': [],
            'DeleteMarkers': [],
            'KeyMarker': '',
            'VersionIdMarker': '',
            'MaxKeys': 1000,
            'IsTruncated': False,
            'Name': 'unversioned-bucket',
            'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId': 'test-request-id'}
        }
        mock_s3_client.list_object_versions.return_value = unversioned_response
        
        result = op.execute_operation(context)
        assert result.success is True
        assert len(result.response['Versions']) == 0
    
    def test_execute_operation_with_delete_markers(self, operation_context_factory, mock_s3_client):
        """Test ListObjectVersions operation with delete markers."""
        op = ListObjectVersionsOperation()
        context = operation_context_factory("ListObjectVersions", {'Bucket': 'versioned-bucket'})
        
        response_with_delete_markers = {
            'Versions': [
                {
                    'Key': 'file1.txt',
                    'VersionId': 'version1',
                    'IsLatest': False,
                    'LastModified': '2023-01-01T00:00:00Z',
                    'Size': 100
                }
            ],
            'DeleteMarkers': [
                {
                    'Key': 'file1.txt',
                    'VersionId': 'delete-marker-1',
                    'IsLatest': True,
                    'LastModified': '2023-01-02T00:00:00Z'
                }
            ],
            'KeyMarker': '',
            'VersionIdMarker': '',
            'MaxKeys': 1000,
            'IsTruncated': False,
            'Name': 'versioned-bucket',
            'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId': 'test-request-id'}
        }
        mock_s3_client.list_object_versions.return_value = response_with_delete_markers
        
        result = op.execute_operation(context)
        assert result.success is True
        assert len(result.response['DeleteMarkers']) == 1
        assert result.response['DeleteMarkers'][0]['Key'] == 'file1.txt'
    
    def test_execute_operation_with_prefix_filter(self, operation_context_factory, mock_s3_client):
        """Test ListObjectVersions operation with prefix filter."""
        op = ListObjectVersionsOperation()
        context = operation_context_factory("ListObjectVersions", {'Bucket': 'versioned-bucket', 'Prefix': 'docs/'})
        result = op.execute_operation(context)
        
        assert result.success is True
        mock_s3_client.list_object_versions.assert_called_once_with(Bucket='versioned-bucket', Prefix='docs/')


class TestGetBucketLocationOperation:
    """Test GetBucketLocationOperation class."""
    
    def test_init(self):
        """Test GetBucketLocationOperation initialization."""
        op = GetBucketLocationOperation()
        assert op.operation_name == "GetBucketLocation"
    
    def test_validate_parameters_success(self):
        """Test parameter validation with required bucket parameter."""
        op = GetBucketLocationOperation()
        params = {'bucket': 'location-test-bucket'}
        result = op.validate_parameters(params)
        assert result == {'Bucket': 'location-test-bucket'}
    
    def test_validate_parameters_missing_bucket(self):
        """Test parameter validation without required bucket parameter."""
        op = GetBucketLocationOperation()
        params = {}
        with pytest.raises(ValueError, match="GetBucketLocation requires 'bucket' parameter"):
            op.validate_parameters(params)
    
    def test_execute_operation_success(self, operation_context_factory, mock_s3_client):
        """Test successful GetBucketLocation operation execution."""
        op = GetBucketLocationOperation()
        context = operation_context_factory("GetBucketLocation", {'Bucket': 'location-test-bucket'})
        result = op.execute_operation(context)
        
        assert result.success is True
        assert result.response['LocationConstraint'] == 'us-west-2'
        mock_s3_client.get_bucket_location.assert_called_once_with(Bucket='location-test-bucket')
    
    def test_execute_operation_client_error_no_such_bucket(self, operation_context_factory, mock_s3_client, client_error_factory):
        """Test GetBucketLocation operation with NoSuchBucket error."""
        op = GetBucketLocationOperation()
        context = operation_context_factory("GetBucketLocation", {'Bucket': 'nonexistent-bucket'})
        
        mock_s3_client.get_bucket_location.side_effect = client_error_factory(
            'NoSuchBucket', 'The specified bucket does not exist', 404
        )
        
        result = op.execute_operation(context)
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'


class TestGetBucketVersioningOperation:
    """Test GetBucketVersioningOperation class."""
    
    def test_init(self):
        """Test GetBucketVersioningOperation initialization."""
        op = GetBucketVersioningOperation()
        assert op.operation_name == "GetBucketVersioning"
    
    def test_validate_parameters_success(self):
        """Test parameter validation with required bucket parameter."""
        op = GetBucketVersioningOperation()
        params = {'bucket': 'versioning-test-bucket'}
        result = op.validate_parameters(params)
        assert result == {'Bucket': 'versioning-test-bucket'}
    
    def test_validate_parameters_missing_bucket(self):
        """Test parameter validation without required bucket parameter."""
        op = GetBucketVersioningOperation()
        params = {}
        with pytest.raises(ValueError, match="GetBucketVersioning requires 'bucket' parameter"):
            op.validate_parameters(params)
    
    def test_execute_operation_success(self, operation_context_factory, mock_s3_client):
        """Test successful GetBucketVersioning operation execution."""
        op = GetBucketVersioningOperation()
        context = operation_context_factory("GetBucketVersioning", {'Bucket': 'versioning-test-bucket'})
        result = op.execute_operation(context)
        
        assert result.success is True
        assert result.response['Status'] == 'Enabled'
        assert result.response['MFADelete'] == 'Disabled'
        mock_s3_client.get_bucket_versioning.assert_called_once_with(Bucket='versioning-test-bucket')
    
    def test_execute_operation_client_error_no_such_bucket(self, operation_context_factory, mock_s3_client, client_error_factory):
        """Test GetBucketVersioning operation with NoSuchBucket error."""
        op = GetBucketVersioningOperation()
        context = operation_context_factory("GetBucketVersioning", {'Bucket': 'nonexistent-bucket'})
        
        mock_s3_client.get_bucket_versioning.side_effect = client_error_factory(
            'NoSuchBucket', 'The specified bucket does not exist', 404
        )
        
        result = op.execute_operation(context)
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'


class TestPutBucketVersioningOperation:
    """Test PutBucketVersioningOperation class."""
    
    def test_init(self):
        """Test PutBucketVersioningOperation initialization."""
        op = PutBucketVersioningOperation()
        assert op.operation_name == "PutBucketVersioning"
    
    def test_validate_parameters_success_enabled(self):
        """Test parameter validation with versioning enabled."""
        op = PutBucketVersioningOperation()
        params = {'bucket': 'versioning-bucket', 'status': 'Enabled'}
        result = op.validate_parameters(params)
        expected = {
            'Bucket': 'versioning-bucket',
            'VersioningConfiguration': {'Status': 'Enabled'}
        }
        assert result == expected
    
    def test_validate_parameters_success_suspended(self):
        """Test parameter validation with versioning suspended."""
        op = PutBucketVersioningOperation()
        params = {'bucket': 'versioning-bucket', 'status': 'Suspended'}
        result = op.validate_parameters(params)
        expected = {
            'Bucket': 'versioning-bucket',
            'VersioningConfiguration': {'Status': 'Suspended'}
        }
        assert result == expected
    
    def test_validate_parameters_with_mfa_delete(self):
        """Test parameter validation with MFA delete configuration."""
        op = PutBucketVersioningOperation()
        params = {
            'bucket': 'versioning-bucket',
            'status': 'Enabled',
            'mfa_delete': 'Enabled',
            'mfa': 'arn:aws:iam::123456789012:mfa/user ABCDEF'
        }
        result = op.validate_parameters(params)
        expected = {
            'Bucket': 'versioning-bucket',
            'VersioningConfiguration': {
                'Status': 'Enabled',
                'MFADelete': 'Enabled'
            },
            'MFA': 'arn:aws:iam::123456789012:mfa/user ABCDEF'
        }
        assert result == expected
    
    def test_validate_parameters_missing_bucket(self):
        """Test parameter validation without required bucket parameter."""
        op = PutBucketVersioningOperation()
        params = {'status': 'Enabled'}
        with pytest.raises(ValueError, match="PutBucketVersioning requires 'bucket' parameter"):
            op.validate_parameters(params)
    
    def test_validate_parameters_missing_status(self):
        """Test parameter validation without required status parameter."""
        op = PutBucketVersioningOperation()
        params = {'bucket': 'versioning-bucket'}
        with pytest.raises(ValueError, match="PutBucketVersioning requires 'status' parameter"):
            op.validate_parameters(params)
    
    def test_validate_parameters_invalid_status(self):
        """Test parameter validation with invalid status value."""
        op = PutBucketVersioningOperation()
        params = {'bucket': 'versioning-bucket', 'status': 'Invalid'}
        with pytest.raises(ValueError, match="Versioning status must be either 'Enabled' or 'Suspended'"):
            op.validate_parameters(params)
    
    def test_validate_parameters_invalid_mfa_delete(self):
        """Test parameter validation with invalid MFA delete value."""
        op = PutBucketVersioningOperation()
        params = {
            'bucket': 'versioning-bucket',
            'status': 'Enabled',
            'mfa_delete': 'Invalid'
        }
        with pytest.raises(ValueError, match="MFA Delete must be either 'Enabled' or 'Disabled'"):
            op.validate_parameters(params)
    
    def test_execute_operation_success(self, operation_context_factory, mock_s3_client):
        """Test successful PutBucketVersioning operation execution."""
        op = PutBucketVersioningOperation()
        parameters = {
            'Bucket': 'versioning-bucket',
            'VersioningConfiguration': {'Status': 'Enabled'}
        }
        context = operation_context_factory("PutBucketVersioning", parameters)
        result = op.execute_operation(context)
        
        assert result.success is True
        mock_s3_client.put_bucket_versioning.assert_called_once_with(**parameters)
    
    def test_execute_operation_client_error_access_denied(self, operation_context_factory, mock_s3_client, client_error_factory):
        """Test PutBucketVersioning operation with AccessDenied error."""
        op = PutBucketVersioningOperation()
        parameters = {
            'Bucket': 'restricted-bucket',
            'VersioningConfiguration': {'Status': 'Enabled'}
        }
        context = operation_context_factory("PutBucketVersioning", parameters)
        
        mock_s3_client.put_bucket_versioning.side_effect = client_error_factory(
            'AccessDenied', 'Access Denied', 403
        )
        
        result = op.execute_operation(context)
        assert result.success is False
        assert result.error_code == 'AccessDenied'


class TestGetBucketTaggingOperation:
    """Test GetBucketTaggingOperation class."""
    
    def test_init(self):
        """Test GetBucketTaggingOperation initialization."""
        op = GetBucketTaggingOperation()
        assert op.operation_name == "GetBucketTagging"
    
    def test_validate_parameters_success(self):
        """Test parameter validation with required bucket parameter."""
        op = GetBucketTaggingOperation()
        params = {'bucket': 'tagged-bucket'}
        result = op.validate_parameters(params)
        assert result == {'Bucket': 'tagged-bucket'}
    
    def test_validate_parameters_missing_bucket(self):
        """Test parameter validation without required bucket parameter."""
        op = GetBucketTaggingOperation()
        params = {}
        with pytest.raises(ValueError, match="GetBucketTagging requires 'bucket' parameter"):
            op.validate_parameters(params)
    
    def test_execute_operation_success(self, operation_context_factory, mock_s3_client):
        """Test successful GetBucketTagging operation execution."""
        op = GetBucketTaggingOperation()
        context = operation_context_factory("GetBucketTagging", {'Bucket': 'tagged-bucket'})
        result = op.execute_operation(context)
        
        assert result.success is True
        assert 'TagSet' in result.response
        assert len(result.response['TagSet']) == 3
        mock_s3_client.get_bucket_tagging.assert_called_once_with(Bucket='tagged-bucket')
    
    def test_execute_operation_no_such_tag_set(self, operation_context_factory, mock_s3_client, client_error_factory):
        """Test GetBucketTagging operation with NoSuchTagSet error (no tags exist)."""
        op = GetBucketTaggingOperation()
        context = operation_context_factory("GetBucketTagging", {'Bucket': 'untagged-bucket'})
        
        mock_s3_client.get_bucket_tagging.side_effect = client_error_factory(
            'NoSuchTagSet', 'The TagSet does not exist', 404
        )
        
        result = op.execute_operation(context)
        assert result.success is True  # Converted to success with empty TagSet
        assert result.response == {'TagSet': []}
    
    def test_execute_operation_client_error_no_such_bucket(self, operation_context_factory, mock_s3_client, client_error_factory):
        """Test GetBucketTagging operation with NoSuchBucket error."""
        op = GetBucketTaggingOperation()
        context = operation_context_factory("GetBucketTagging", {'Bucket': 'nonexistent-bucket'})
        
        mock_s3_client.get_bucket_tagging.side_effect = client_error_factory(
            'NoSuchBucket', 'The specified bucket does not exist', 404
        )
        
        result = op.execute_operation(context)
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'


class TestPutBucketTaggingOperation:
    """Test PutBucketTaggingOperation class."""
    
    def test_init(self):
        """Test PutBucketTaggingOperation initialization."""
        op = PutBucketTaggingOperation()
        assert op.operation_name == "PutBucketTagging"
    
    def test_validate_parameters_success(self, sample_tags_dict):
        """Test parameter validation with required parameters."""
        op = PutBucketTaggingOperation()
        params = {'bucket': 'tagging-bucket', 'tags': sample_tags_dict}
        result = op.validate_parameters(params)
        
        expected = {
            'Bucket': 'tagging-bucket',
            'Tagging': {
                'TagSet': [
                    {'Key': 'Environment', 'Value': 'Production'},
                    {'Key': 'Team', 'Value': 'DevOps'},
                    {'Key': 'Project', 'Value': 'S3Tester'}
                ]
            }
        }
        assert result == expected
    
    def test_validate_parameters_missing_bucket(self, sample_tags_dict):
        """Test parameter validation without required bucket parameter."""
        op = PutBucketTaggingOperation()
        params = {'tags': sample_tags_dict}
        with pytest.raises(ValueError, match="PutBucketTagging requires 'bucket' parameter"):
            op.validate_parameters(params)
    
    def test_validate_parameters_missing_tags(self):
        """Test parameter validation without required tags parameter."""
        op = PutBucketTaggingOperation()
        params = {'bucket': 'tagging-bucket'}
        with pytest.raises(ValueError, match="PutBucketTagging requires 'tags' parameter"):
            op.validate_parameters(params)
    
    def test_validate_parameters_invalid_tags_type(self):
        """Test parameter validation with invalid tags type."""
        op = PutBucketTaggingOperation()
        params = {'bucket': 'tagging-bucket', 'tags': 'invalid'}
        with pytest.raises(ValueError, match="Tags must be provided as a dictionary"):
            op.validate_parameters(params)
    
    def test_validate_parameters_tags_with_numeric_values(self):
        """Test parameter validation with numeric tag values."""
        op = PutBucketTaggingOperation()
        params = {
            'bucket': 'tagging-bucket',
            'tags': {'Environment': 'Production', 'Version': 1.0, 'Count': 42}
        }
        result = op.validate_parameters(params)
        
        expected_tags = [
            {'Key': 'Environment', 'Value': 'Production'},
            {'Key': 'Version', 'Value': '1.0'},
            {'Key': 'Count', 'Value': '42'}
        ]
        assert result['Tagging']['TagSet'] == expected_tags
    
    def test_execute_operation_success(self, operation_context_factory, mock_s3_client, sample_tags_list):
        """Test successful PutBucketTagging operation execution."""
        op = PutBucketTaggingOperation()
        parameters = {
            'Bucket': 'tagging-bucket',
            'Tagging': {'TagSet': sample_tags_list}
        }
        context = operation_context_factory("PutBucketTagging", parameters)
        result = op.execute_operation(context)
        
        assert result.success is True
        mock_s3_client.put_bucket_tagging.assert_called_once_with(**parameters)
    
    def test_execute_operation_client_error_access_denied(self, operation_context_factory, mock_s3_client, client_error_factory, sample_tags_list):
        """Test PutBucketTagging operation with AccessDenied error."""
        op = PutBucketTaggingOperation()
        parameters = {
            'Bucket': 'restricted-bucket',
            'Tagging': {'TagSet': sample_tags_list}
        }
        context = operation_context_factory("PutBucketTagging", parameters)
        
        mock_s3_client.put_bucket_tagging.side_effect = client_error_factory(
            'AccessDenied', 'Access Denied', 403
        )
        
        result = op.execute_operation(context)
        assert result.success is False
        assert result.error_code == 'AccessDenied'
    
    def test_execute_operation_empty_tags(self, operation_context_factory, mock_s3_client):
        """Test PutBucketTagging operation with empty tags."""
        op = PutBucketTaggingOperation()
        parameters = {
            'Bucket': 'tagging-bucket',
            'Tagging': {'TagSet': []}
        }
        context = operation_context_factory("PutBucketTagging", parameters)
        result = op.execute_operation(context)
        
        assert result.success is True
        mock_s3_client.put_bucket_tagging.assert_called_once_with(**parameters)


class TestDeleteBucketTaggingOperation:
    """Test DeleteBucketTaggingOperation class."""
    
    def test_init(self):
        """Test DeleteBucketTaggingOperation initialization."""
        op = DeleteBucketTaggingOperation()
        assert op.operation_name == "DeleteBucketTagging"
    
    def test_validate_parameters_success(self):
        """Test parameter validation with required bucket parameter."""
        op = DeleteBucketTaggingOperation()
        params = {'bucket': 'tagged-bucket'}
        result = op.validate_parameters(params)
        assert result == {'Bucket': 'tagged-bucket'}
    
    def test_validate_parameters_missing_bucket(self):
        """Test parameter validation without required bucket parameter."""
        op = DeleteBucketTaggingOperation()
        params = {}
        with pytest.raises(ValueError, match="DeleteBucketTagging requires 'bucket' parameter"):
            op.validate_parameters(params)
    
    def test_execute_operation_success(self, operation_context_factory, mock_s3_client):
        """Test successful DeleteBucketTagging operation execution."""
        op = DeleteBucketTaggingOperation()
        context = operation_context_factory("DeleteBucketTagging", {'Bucket': 'tagged-bucket'})
        result = op.execute_operation(context)
        
        assert result.success is True
        mock_s3_client.delete_bucket_tagging.assert_called_once_with(Bucket='tagged-bucket')
    
    def test_execute_operation_client_error_no_such_bucket(self, operation_context_factory, mock_s3_client, client_error_factory):
        """Test DeleteBucketTagging operation with NoSuchBucket error."""
        op = DeleteBucketTaggingOperation()
        context = operation_context_factory("DeleteBucketTagging", {'Bucket': 'nonexistent-bucket'})
        
        mock_s3_client.delete_bucket_tagging.side_effect = client_error_factory(
            'NoSuchBucket', 'The specified bucket does not exist', 404
        )
        
        result = op.execute_operation(context)
        assert result.success is False
        assert result.error_code == 'NoSuchBucket'
    
    def test_execute_operation_already_no_tags(self, operation_context_factory, mock_s3_client, client_error_factory):
        """Test DeleteBucketTagging operation when no tags exist."""
        op = DeleteBucketTaggingOperation()
        context = operation_context_factory("DeleteBucketTagging", {'Bucket': 'untagged-bucket'})
        
        # Some implementations may return NoSuchTagSet, others may succeed
        mock_s3_client.delete_bucket_tagging.side_effect = client_error_factory(
            'NoSuchTagSet', 'The TagSet does not exist', 404
        )
        
        result = op.execute_operation(context)
        assert result.success is False
        assert result.error_code == 'NoSuchTagSet'
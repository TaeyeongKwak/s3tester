"""Shared fixtures for operations tests."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock
from botocore.exceptions import ClientError

from s3tester.operations.base import OperationContext
from s3tester.config.models import FileReference


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client for testing."""
    client = MagicMock()
    
    # Set default successful responses
    client.put_object.return_value = {
        'ETag': '"d41d8cd98f00b204e9800998ecf8427e"',
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': 'test-request-id'
        }
    }
    
    # Mock Body object for GetObject
    mock_body = MagicMock()
    mock_body.read.return_value = b"Hello, World!"
    
    client.get_object.return_value = {
        'Body': mock_body,
        'ContentLength': 13,
        'ContentType': 'text/plain',
        'ETag': '"d41d8cd98f00b204e9800998ecf8427e"',
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': 'test-request-id'
        }
    }
    
    client.delete_object.return_value = {
        'ResponseMetadata': {
            'HTTPStatusCode': 204,
            'RequestId': 'test-request-id'
        }
    }
    
    client.head_object.return_value = {
        'ContentLength': 13,
        'ContentType': 'text/plain',
        'ETag': '"d41d8cd98f00b204e9800998ecf8427e"',
        'LastModified': '2023-01-01T00:00:00Z',
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': 'test-request-id'
        }
    }
    
    # Bucket operations mock responses
    client.create_bucket.return_value = {
        'Location': '/test-bucket',
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': 'test-request-id'
        }
    }
    
    client.delete_bucket.return_value = {
        'ResponseMetadata': {
            'HTTPStatusCode': 204,
            'RequestId': 'test-request-id'
        }
    }
    
    client.list_buckets.return_value = {
        'Buckets': [
            {
                'Name': 'bucket1',
                'CreationDate': '2023-01-01T00:00:00Z'
            },
            {
                'Name': 'bucket2', 
                'CreationDate': '2023-01-02T00:00:00Z'
            }
        ],
        'Owner': {
            'ID': 'owner-id-12345',
            'DisplayName': 'test-owner'
        },
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': 'test-request-id'
        }
    }
    
    client.head_bucket.return_value = {
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': 'test-request-id'
        }
    }
    
    # Bucket policy operations mock responses
    client.get_bucket_policy.return_value = {
        'Policy': json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::test-bucket/*"
                }
            ]
        }),
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': 'test-request-id'
        }
    }
    
    client.put_bucket_policy.return_value = {
        'ResponseMetadata': {
            'HTTPStatusCode': 204,
            'RequestId': 'test-request-id'
        }
    }
    
    client.delete_bucket_policy.return_value = {
        'ResponseMetadata': {
            'HTTPStatusCode': 204,
            'RequestId': 'test-request-id'
        }
    }
    
    # Bucket extended operations mock responses
    client.list_objects_v2.return_value = {
        'Contents': [
            {
                'Key': 'file1.txt',
                'LastModified': '2023-01-01T00:00:00Z',
                'ETag': '"d41d8cd98f00b204e9800998ecf8427e"',
                'Size': 100,
                'StorageClass': 'STANDARD'
            },
            {
                'Key': 'file2.txt',
                'LastModified': '2023-01-02T00:00:00Z', 
                'ETag': '"b2ca678b777f2fdf1e0b2e8d3c5b5c6c"',
                'Size': 200,
                'StorageClass': 'STANDARD'
            }
        ],
        'KeyCount': 2,
        'MaxKeys': 1000,
        'IsTruncated': False,
        'Name': 'test-bucket',
        'Prefix': '',
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': 'test-request-id'
        }
    }
    
    client.list_object_versions.return_value = {
        'Versions': [
            {
                'Key': 'file1.txt',
                'VersionId': 'version1',
                'IsLatest': True,
                'LastModified': '2023-01-01T00:00:00Z',
                'Size': 100
            }
        ],
        'DeleteMarkers': [],
        'KeyMarker': '',
        'VersionIdMarker': '',
        'MaxKeys': 1000,
        'IsTruncated': False,
        'Name': 'test-bucket',
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': 'test-request-id'
        }
    }
    
    client.get_bucket_location.return_value = {
        'LocationConstraint': 'us-west-2',
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': 'test-request-id'
        }
    }
    
    client.get_bucket_versioning.return_value = {
        'Status': 'Enabled',
        'MFADelete': 'Disabled',
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': 'test-request-id'
        }
    }
    
    client.put_bucket_versioning.return_value = {
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': 'test-request-id'
        }
    }
    
    client.get_bucket_tagging.return_value = {
        'TagSet': [
            {'Key': 'Environment', 'Value': 'Production'},
            {'Key': 'Team', 'Value': 'DevOps'},
            {'Key': 'Project', 'Value': 'S3Tester'}
        ],
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
            'RequestId': 'test-request-id'
        }
    }
    
    client.put_bucket_tagging.return_value = {
        'ResponseMetadata': {
            'HTTPStatusCode': 204,
            'RequestId': 'test-request-id'
        }
    }
    
    client.delete_bucket_tagging.return_value = {
        'ResponseMetadata': {
            'HTTPStatusCode': 204,
            'RequestId': 'test-request-id'
        }
    }
    
    return client


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        yield temp_path


@pytest.fixture
def sample_text_file(temp_config_dir):
    """Create a sample text file for testing."""
    file_path = temp_config_dir / "sample.txt"
    content = "Hello, World!"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_json_file(temp_config_dir):
    """Create a sample JSON file for testing."""
    file_path = temp_config_dir / "sample.json"
    content = {"message": "Hello, World!", "type": "greeting"}
    file_path.write_text(json.dumps(content))
    return file_path


@pytest.fixture
def sample_binary_file(temp_config_dir):
    """Create a sample binary file for testing."""
    file_path = temp_config_dir / "sample.bin"
    content = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09'
    file_path.write_bytes(content)
    return file_path


@pytest.fixture
def operation_context_factory(mock_s3_client, temp_config_dir):
    """Factory function for creating OperationContext instances."""
    def create_context(operation_name: str, parameters: dict, dry_run: bool = False):
        return OperationContext(
            s3_client=mock_s3_client,
            operation_name=operation_name,
            parameters=parameters,
            config_dir=temp_config_dir,
            dry_run=dry_run
        )
    return create_context


def create_client_error(error_code: str, error_message: str, status_code: int = 400):
    """Helper function to create ClientError for testing."""
    error_response = {
        'Error': {
            'Code': error_code,
            'Message': error_message
        },
        'ResponseMetadata': {
            'HTTPStatusCode': status_code,
            'RequestId': 'test-request-id'
        }
    }
    return ClientError(error_response, 'operation_name')


@pytest.fixture
def client_error_factory():
    """Factory function for creating ClientError instances."""
    return create_client_error


@pytest.fixture
def valid_bucket_names():
    """List of valid bucket names for testing."""
    return [
        'test-bucket',
        'my-test-bucket-123',
        'bucket.with.dots',
        'b' * 63  # maximum length
    ]


@pytest.fixture
def invalid_bucket_names():
    """List of invalid bucket names for testing."""
    return [
        'Test-Bucket',  # uppercase
        'test_bucket',  # underscore
        'te',  # too short
        'b' * 64,  # too long
        'test..bucket',  # consecutive dots
        '-test-bucket',  # starts with dash
        'test-bucket-',  # ends with dash
    ]


@pytest.fixture
def valid_object_keys():
    """List of valid object keys for testing."""
    return [
        'test-key',
        'folder/subfolder/file.txt',
        'special-chars!@#$%^&*()_+.txt',
        'unicode-文件名.txt',
        'a' * 1024  # maximum length
    ]


@pytest.fixture
def invalid_object_keys():
    """List of invalid object keys for testing."""
    return [
        '',  # empty
        'a' * 1025,  # too long
    ]


@pytest.fixture
def aws_regions():
    """List of AWS regions for testing."""
    return [
        'us-east-1',
        'us-west-2',
        'eu-west-1',
        'eu-central-1',
        'ap-southeast-1',
        'ap-northeast-1'
    ]


@pytest.fixture
def s3_acl_options():
    """List of S3 ACL options for testing."""
    return [
        'private',
        'public-read',
        'public-read-write',
        'authenticated-read',
        'bucket-owner-read',
        'bucket-owner-full-control'
    ]


@pytest.fixture
def sample_bucket_policy_dict():
    """Sample S3 bucket policy as dictionary for testing."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::test-bucket/*"
            }
        ]
    }


@pytest.fixture
def sample_bucket_policy_json(sample_bucket_policy_dict):
    """Sample S3 bucket policy as JSON string for testing."""
    return json.dumps(sample_bucket_policy_dict)


@pytest.fixture
def complex_bucket_policy_dict():
    """Complex S3 bucket policy as dictionary for testing."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::test-bucket/*"
            },
            {
                "Sid": "AllowSpecificUser",
                "Effect": "Allow",
                "Principal": {"AWS": "arn:aws:iam::123456789012:user/testuser"},
                "Action": ["s3:GetObject", "s3:PutObject"],
                "Resource": "arn:aws:s3:::test-bucket/private/*",
                "Condition": {
                    "StringEquals": {
                        "s3:x-amz-server-side-encryption": "AES256"
                    }
                }
            }
        ]
    }


@pytest.fixture
def empty_bucket_policy_dict():
    """Empty S3 bucket policy as dictionary for testing."""
    return {
        "Version": "2012-10-17",
        "Statement": []
    }


@pytest.fixture
def default_object_list():
    """Default object list for list operations testing."""
    return [
        {
            'Key': 'file1.txt',
            'LastModified': '2023-01-01T00:00:00Z',
            'ETag': '"d41d8cd98f00b204e9800998ecf8427e"',
            'Size': 100,
            'StorageClass': 'STANDARD'
        },
        {
            'Key': 'file2.txt',
            'LastModified': '2023-01-02T00:00:00Z',
            'ETag': '"b2ca678b777f2fdf1e0b2e8d3c5b5c6c"',
            'Size': 200,
            'StorageClass': 'STANDARD'
        }
    ]


@pytest.fixture
def bucket_versions():
    """Sample bucket versions for testing."""
    return [
        {
            'Key': 'file1.txt',
            'VersionId': 'version1',
            'IsLatest': True,
            'LastModified': '2023-01-01T00:00:00Z',
            'Size': 100
        },
        {
            'Key': 'file1.txt',
            'VersionId': 'version2',
            'IsLatest': False,
            'LastModified': '2022-12-01T00:00:00Z',
            'Size': 95
        }
    ]


@pytest.fixture
def sample_tags_dict():
    """Sample tags dictionary for testing."""
    return {
        'Environment': 'Production',
        'Team': 'DevOps',
        'Project': 'S3Tester'
    }


@pytest.fixture
def sample_tags_list(sample_tags_dict):
    """Sample tags list for testing."""
    return [{'Key': k, 'Value': v} for k, v in sample_tags_dict.items()]
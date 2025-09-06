#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import boto3
import json
from pathlib import Path
from moto import mock_aws
from s3tester.integration.facade import S3TesterFacade
from s3tester.config.models import S3TestConfiguration
from s3tester.core.engine import S3TestExecutionEngine
from tests.test_utils import generate_test_bucket_name


@pytest.fixture
def aws_credentials():
    """Mocked AWS credentials for moto."""
    return {
        "access_key": "testing",
        "secret_key": "testing",
        "region": "us-east-1"
    }


@pytest.fixture
def s3_client(aws_credentials):
    """Create mocked S3 client."""
    with mock_aws():
        s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_credentials["access_key"],
            aws_secret_access_key=aws_credentials["secret_key"],
            region_name=aws_credentials["region"]
        )
        yield s3


@pytest.fixture
def test_bucket(s3_client):
    """Create a test bucket in mocked S3."""
    bucket_name = generate_test_bucket_name()
    s3_client.create_bucket(Bucket=bucket_name)
    yield bucket_name
    
    # Cleanup bucket after test
    try:
        # List and delete all objects
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
        # Delete the bucket
        s3_client.delete_bucket(Bucket=bucket_name)
    except Exception as e:
        # Just log the error, don't fail the test
        import logging
        logging.warning(f"Failed to clean up bucket {bucket_name}: {e}")


@pytest.fixture
def test_config(aws_credentials, test_bucket):
    """Create a test configuration."""
    config_dict = {
        "config": {
            "endpoint_url": "http://localhost:5000",
            "region": aws_credentials["region"],
            "path_style": True,
            "credentials": [
                {
                    "name": "test-creds",
                    "access_key": aws_credentials["access_key"],
                    "secret_key": aws_credentials["secret_key"]
                }
            ]
        },
        "test_cases": {
            "parallel": False,
            "groups": [
                {
                    "name": "integration-test-group",
                    "credential": "test-creds",
                    "test": [
                        {
                            "operation": "PutObject",
                            "parameters": {
                                "bucket": test_bucket,
                                "key": "test-key-1",
                                "body": "Hello, World!"
                            },
                            "expected_result": {
                                "success": True
                            }
                        },
                        {
                            "operation": "GetObject", 
                            "parameters": {
                                "bucket": test_bucket,
                                "key": "test-key-1"
                            },
                            "expected_result": {
                                "success": True
                            }
                        }
                    ]
                }
            ]
        }
    }
    
    return S3TestConfiguration(**config_dict)


@pytest.fixture
def temp_config_file(tmp_path, test_config):
    """Save test config to a temporary file."""
    config_file = tmp_path / "test_config.json"
    with open(config_file, "w") as f:
        json.dump(test_config.model_dump(), f)
    return str(config_file)

@mock_aws
class TestS3Operations:
    """Integration tests for S3 operations."""
    
    def test_put_and_get_object(self, aws_credentials, test_bucket):
        """Test putting and getting an object from S3."""
        # Create S3 client
        s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_credentials["access_key"],
            aws_secret_access_key=aws_credentials["secret_key"],
            region_name=aws_credentials["region"]
        )
        
        # Put an object
        s3.put_object(
            Bucket=test_bucket,
            Key="test-key",
            Body="Hello, Integration Test!"
        )
        
        # Get the object
        response = s3.get_object(
            Bucket=test_bucket,
            Key="test-key"
        )
        
        # Verify content
        body = response["Body"].read().decode("utf-8")
        assert body == "Hello, Integration Test!"

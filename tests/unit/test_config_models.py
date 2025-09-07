#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from pydantic import ValidationError
from s3tester.config.models import (
    S3TestConfiguration, GlobalConfig, CredentialSet, 
    S3TestCases, S3TestGroup, Operation, ExpectedResult
)


class TestConfigModels:
    """Test cases for config model classes."""
    
    def test_credential_set_validation(self):
        """Test credential set validation logic."""
        # Valid credential set
        valid_creds = CredentialSet(
            name="test-creds",
            access_key="test_access_key",
            secret_key="test_secret_key",
            session_token=None,
            region="us-west-2"
        )
        assert valid_creds.access_key == "test_access_key"
        assert valid_creds.secret_key == "test_secret_key"
        assert valid_creds.name == "test-creds"
        
        # Test validation error when name format is invalid
        with pytest.raises(ValidationError):
            CredentialSet(
                name="invalid name with spaces",
                access_key="test_access_key",
                secret_key="test_secret_key"
            )
            
        # Test validation for empty credentials
        with pytest.raises(ValidationError):
            CredentialSet(
                name="empty-creds"
            )
    
    def test_global_config_validation(self):
        """Test global configuration validation."""
        valid_creds = CredentialSet(
            name="test-cred",
            access_key="test_access_key",
            secret_key="test_secret_key"
        )
        
        valid_global = GlobalConfig(
            endpoint_url="https://s3.amazonaws.com",
            region="us-west-2",
            path_style=False,
            credentials=[valid_creds]
        )
        
        assert valid_global.endpoint_url == "https://s3.amazonaws.com"
        assert valid_global.region == "us-west-2"
        assert len(valid_global.credentials) == 1
        
        # Test validation of endpoint URL
        with pytest.raises(ValidationError):
            GlobalConfig(
                endpoint_url="invalid-url",
                region="us-west-2",
                credentials=[valid_creds]
            )
            
        # Test validation of unique credential names
        with pytest.raises(ValueError):
            duplicate_creds = [
                CredentialSet(
                    name="same-name",
                    access_key="key1",
                    secret_key="secret1"
                ),
                CredentialSet(
                    name="same-name",
                    access_key="key2",
                    secret_key="secret2"
                )
            ]
            GlobalConfig(
                endpoint_url="https://s3.amazonaws.com",
                region="us-west-2",
                credentials=duplicate_creds
            )
    
    def test_test_configuration_validation(self):
        """Test test configuration validation."""
        # 유효한 credential 생성
        valid_cred = CredentialSet(
            name="test-cred",
            access_key="test_access_key",
            secret_key="test_secret_key"
        )
        
        # 유효한 GlobalConfig 생성
        valid_global = GlobalConfig(
            endpoint_url="https://s3.amazonaws.com",
            region="us-west-2",
            path_style=False,
            credentials=[valid_cred]
        )
        
        # 유효한 Operation 생성
        test_operation = Operation(
            operation="CreateBucket",
            parameters={"bucket_name": "test-bucket"},
            expected_result=ExpectedResult(success=True)
        )
        
        # 유효한 S3TestGroup 생성
        test_group = S3TestGroup(
            name="test-group",
            credential="test-cred",
            test=[test_operation]
        )
        
        # 유효한 S3TestCases 생성
        test_cases = S3TestCases(
            groups=[test_group]
        )
        
        # 유효한 S3TestConfiguration 생성
        valid_config = S3TestConfiguration(
            config=valid_global,
            test_cases=test_cases
        )
        
        assert valid_config.config.endpoint_url == "https://s3.amazonaws.com"
        assert len(valid_config.test_cases.groups) == 1
        assert valid_config.test_cases.groups[0].name == "test-group"
        
        # 유효하지 않은 credential 참조 테스트
        invalid_group = S3TestGroup(
            name="invalid-group",
            credential="non-existent-cred",  # 존재하지 않는 credential 이름
            test=[test_operation]
        )
        
        # 현재는 런타임에만 credential 검증이 이루어지므로 이 테스트는 스킵
        # S3TestCases에서 그룹 이름 중복 테스트
        with pytest.raises(ValueError):
            S3TestCases(
                groups=[test_group, test_group]  # 동일한 이름의 그룹이 중복
            )

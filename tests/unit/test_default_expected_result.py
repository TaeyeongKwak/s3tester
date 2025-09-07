#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from s3tester.config.models import (
    Operation, ExpectedResult
)


class TestDefaultExpectedResult:
    """Test cases for default ExpectedResult behavior."""
    
    def test_expected_result_default_value(self):
        """Test that ExpectedResult has default success=True."""
        # Create an ExpectedResult without specifying success
        result = ExpectedResult()
        assert result.success is True
        assert result.error_code is None
        assert result.response_contains is None
    
    def test_operation_default_expected_result(self):
        """Test that Operation creates default ExpectedResult when not specified."""
        # Create an Operation without explicitly specifying expected_result
        operation = Operation(
            operation="ListBuckets",
            parameters={}
        )
        
        # Verify that expected_result was created with default success=True
        assert operation.expected_result is not None
        assert operation.expected_result.success is True
        assert operation.expected_result.error_code is None
        
    def test_operation_custom_expected_result(self):
        """Test that Operation respects custom ExpectedResult when provided."""
        # Create an Operation with explicitly specified expected_result
        expected = ExpectedResult(success=False, error_code="BucketNotEmpty")
        operation = Operation(
            operation="DeleteBucket",
            parameters={"Bucket": "test-bucket"},
            expected_result=expected
        )
        
        # Verify that expected_result was set correctly
        assert operation.expected_result is not None
        assert operation.expected_result.success is False
        assert operation.expected_result.error_code == "BucketNotEmpty"

    def test_expected_result_validation(self):
        """Test ExpectedResult validation still works properly."""
        # Success=True with error_code should fail
        with pytest.raises(ValueError):
            ExpectedResult(success=True, error_code="BucketNotEmpty")
        
        # Success=False without error_code should fail
        with pytest.raises(ValueError):
            ExpectedResult(success=False)
        
        # These should be valid
        assert ExpectedResult(success=True).success is True
        assert ExpectedResult(success=False, error_code="NoSuchBucket").error_code == "NoSuchBucket"

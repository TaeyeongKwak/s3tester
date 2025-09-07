#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from unittest.mock import MagicMock, patch
from s3tester.operations.base import S3Operation
from tests.test_utils import generate_test_bucket_name, generate_test_key_name


class TestOperationRegistry:
    """Test cases for operation registration."""
    
    def test_mock_operation_registry(self):
        """Test a mock operation registry functionality."""
        # 임시로 OperationRegistry 클래스 구현
        class OperationRegistry:
            def __init__(self):
                self.operations = {}
                
            def register(self, name, operation_class):
                self.operations[name] = operation_class
                
            def get_operation(self, name):
                return self.operations.get(name)
                
            def get_available_operations(self):
                return list(self.operations.keys())
        
        # Create mock operation classes
        class MockPutObjectOperation:
            pass
            
        class MockGetObjectOperation:
            pass
        
        # Register operations
        registry = OperationRegistry()
        registry.register("put_object", MockPutObjectOperation)
        registry.register("get_object", MockGetObjectOperation)
        
        # Verify operations can be retrieved
        assert registry.get_operation("put_object") == MockPutObjectOperation
        assert registry.get_operation("get_object") == MockGetObjectOperation
        
        # Verify invalid operation returns None
        assert registry.get_operation("invalid_operation") is None
        
        # Verify available operations list
        available_ops = registry.get_available_operations()
        assert "put_object" in available_ops
        assert "get_object" in available_ops
        assert len(available_ops) == 2


class TestS3Operation:
    """Test cases for S3Operation."""
    
    def test_execute(self):
        """Test the base execute method."""
        # Create a concrete operation class for testing
        class TestOperation(S3Operation):
            def __init__(self):
                super().__init__("test_operation")
                
            def validate_parameters(self, parameters):
                return parameters
                
            def execute_operation(self, context):
                from s3tester.operations.base import OperationResult
                return OperationResult(success=True, duration=0.1, 
                                      response={"test_result": "success"})
        
        # Mock S3 client
        mock_client = MagicMock()
        
        # Create operation instance and execute
        operation = TestOperation()
        from s3tester.operations.base import OperationContext
        from pathlib import Path
        
        bucket_name = generate_test_bucket_name()
        key_name = generate_test_key_name()
        
        context = OperationContext(
            s3_client=mock_client,
            operation_name="test_operation",
            parameters={"bucket": bucket_name, "key": key_name},
            config_dir=Path(".")
        )
        
        result = operation.execute(context)
        
        # Verify result contains standard fields plus operation result
        assert result.success is True
        assert result.duration >= 0.0
        assert result.response is not None
        assert result.response["test_result"] == "success"

class TestMockS3Operations:
    """Test cases for mock S3 operations."""
    
    def test_put_object_operation(self):
        """Test a mock put_object operation."""
        # 기존 PutObjectOperation을 모방한 테스트용 클래스 생성
        class MockPutObjectOperation(S3Operation):
            def __init__(self):
                super().__init__("put_object")
            
            def validate_parameters(self, parameters):
                if "bucket" not in parameters:
                    raise ValueError("Missing required parameter: bucket")
                if "key" not in parameters:
                    raise ValueError("Missing required parameter: key")
                return parameters
            
            def execute_operation(self, context):
                from s3tester.operations.base import OperationResult
                # 실제 실행은 하지 않고 성공 결과를 반환
                client = context.s3_client
                params = context.parameters
                
                try:
                    # S3 클라이언트로 put_object 메서드 호출
                    response = client.put_object(
                        Bucket=params["bucket"],
                        Key=params["key"],
                        Body=params.get("content", "")
                    )
                    
                    return OperationResult(
                        success=True,
                        duration=0.1,
                        response=response
                    )
                except Exception as e:
                    return OperationResult(
                        success=False,
                        duration=0.1,
                        error_code="ExecutionError",
                        error_message=str(e),
                        raw_exception=e
                    )
        
        # Mock S3 client
        mock_client = MagicMock()
        mock_client.put_object.return_value = {
            "ETag": "\"etag123456789\"",
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }
        
        # 테스트 실행
        from s3tester.operations.base import OperationContext
        from pathlib import Path
        
        bucket_name = generate_test_bucket_name()
        key_name = generate_test_key_name()
        
        operation = MockPutObjectOperation()
        context = OperationContext(
            s3_client=mock_client,
            operation_name="put_object",
            parameters={
                "bucket": bucket_name,
                "key": key_name,
                "content": "Hello, World!"
            },
            config_dir=Path(".")
        )
        
        result = operation.execute(context)
        
        # 결과 검증
        assert result.success is True
        assert result.response is not None
        assert "ETag" in result.response
        assert result.response["ETag"] == "\"etag123456789\""
        
        # 클라이언트가 올바르게 호출되었는지 확인
        mock_client.put_object.assert_called_with(
            Bucket=bucket_name,
            Key=key_name,
            Body="Hello, World!"
        )
    
    def test_get_object_operation(self):
        """Test a mock get_object operation."""
        # 기존 GetObjectOperation을 모방한 테스트용 클래스 생성
        class MockGetObjectOperation(S3Operation):
            def __init__(self):
                super().__init__("get_object")
            
            def validate_parameters(self, parameters):
                if "bucket" not in parameters:
                    raise ValueError("Missing required parameter: bucket")
                if "key" not in parameters:
                    raise ValueError("Missing required parameter: key")
                return parameters
            
            def execute_operation(self, context):
                from s3tester.operations.base import OperationResult
                # 실제 실행은 하지 않고 성공 결과를 반환
                client = context.s3_client
                params = context.parameters
                
                try:
                    # S3 클라이언트로 get_object 메서드 호출
                    response = client.get_object(
                        Bucket=params["bucket"],
                        Key=params["key"]
                    )
                    
                    return OperationResult(
                        success=True,
                        duration=0.1,
                        response=response
                    )
                except Exception as e:
                    return OperationResult(
                        success=False,
                        duration=0.1,
                        error_code="ExecutionError",
                        error_message=str(e),
                        raw_exception=e
                    )
        
        # Mock 응답 생성
        mock_body = MagicMock()
        mock_body.read.return_value = b"Hello, World!"
        
        # Mock S3 client
        mock_client = MagicMock()
        mock_client.get_object.return_value = {
            "Body": mock_body,
            "ContentLength": 13,
            "ETag": "\"etag123456789\"",
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }
        
        # 테스트 실행
        from s3tester.operations.base import OperationContext
        from pathlib import Path
        
        bucket_name = generate_test_bucket_name()
        key_name = generate_test_key_name()
        
        operation = MockGetObjectOperation()
        context = OperationContext(
            s3_client=mock_client,
            operation_name="get_object",
            parameters={
                "bucket": bucket_name,
                "key": key_name
            },
            config_dir=Path(".")
        )
        
        result = operation.execute(context)
        
        # 결과 검증
        assert result.success is True
        assert result.response is not None
        assert "ContentLength" in result.response
        assert result.response["ContentLength"] == 13
        assert "ETag" in result.response
        assert result.response["ETag"] == "\"etag123456789\""
        
        # 클라이언트가 올바르게 호출되었는지 확인
        mock_client.get_object.assert_called_with(
            Bucket=bucket_name,
            Key=key_name
        )

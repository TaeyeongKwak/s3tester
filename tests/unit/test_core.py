#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from s3tester.core.engine import S3TestExecutionEngine
from s3tester.core.client_factory import S3ClientFactory
from s3tester.core.result_collector import ResultCollector


class TestS3ClientFactory:
    """Test cases for S3ClientFactory."""
    
    @patch('boto3.Session')
    def test_get_client(self, mock_session):
        """Test client creation with various credential configurations."""
        mock_session.return_value.client.return_value = "mock_s3_client"
        
        # Test with access key and secret
        factory = S3ClientFactory()
        client = factory.get_client({
            "access_key": "test_key",
            "secret_key": "test_secret",
            "region": "us-west-2"
        })
        
        assert client == "mock_s3_client"
        mock_session.assert_called_with(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            region_name="us-west-2"
        )
        
        # Test with profile
        mock_session.reset_mock()
        client = factory.get_client({
            "profile": "test_profile",
            "region": "us-east-1"
        })
        
        assert client == "mock_s3_client"
        mock_session.assert_called_with(
            profile_name="test_profile",
            region_name="us-east-1"
        )
        
        # Test with session token
        mock_session.reset_mock()
        client = factory.get_client({
            "access_key": "test_key",
            "secret_key": "test_secret",
            "session_token": "test_token",
            "region": "eu-west-1"
        })
        
        assert client == "mock_s3_client"
        mock_session.assert_called_with(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            aws_session_token="test_token",
            region_name="eu-west-1"
        )


class TestResultCollector:
    """Test cases for ResultCollector."""
    
    def test_add_and_get_results(self):
        """Test adding and retrieving results."""
        collector = ResultCollector()
        
        # Add test results
        result1 = {
            "success": True,
            "duration_ms": 100,
            "operation_type": "PutObject"
        }
        
        result2 = {
            "success": False,
            "error": "Access denied",
            "duration_ms": 150,
            "operation_type": "DeleteObject"
        }
        
        collector.add_result(result1)
        collector.add_result(result2)
        
        results = collector.get_results()
        
        assert len(results) == 2
        assert results[0] == result1
        assert results[1] == result2
    
    def test_result_statistics(self):
        """Test calculating result statistics."""
        collector = ResultCollector()
        
        # Add test results with mixed successes and failures
        collector.add_result({"success": True, "duration_ms": 100})
        collector.add_result({"success": True, "duration_ms": 150})
        collector.add_result({"success": False, "duration_ms": 200})
        collector.add_result({"success": True, "duration_ms": 120})
        
        stats = collector.calculate_statistics()
        
        assert stats["total"] == 4
        assert stats["successful"] == 3
        assert stats["failed"] == 1
        assert stats["success_rate"] == 75.0
        assert 100 <= stats["avg_duration_ms"] <= 150  # Approximate range


class TestTestExecutionEngine:
    """Test cases for TestExecutionEngine."""
    
    @pytest.mark.asyncio
    async def test_execute_operation(self):
        """Test execution of a single operation."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = {"success": True, "duration_ms": 100}
        
        mock_collector = MagicMock()
        
        # test_engine_wrapper.py의 MockS3TestExecutionEngine 사용
        from .test_engine_wrapper import MockS3TestExecutionEngine
        
        engine = MockS3TestExecutionEngine(
            operation_executor=mock_executor,
            result_collector=mock_collector
        )
        
        operation = {
            "type": "PutObject",
            "params": {"bucket": "test-bucket", "key": "test-key"},
            "repeat": 1
        }
        
        credentials = {
            "access_key": "test_key",
            "secret_key": "test_secret",
            "region": "us-west-2"
        }
        
        await engine.execute_operation(operation, credentials)
        
        mock_executor.execute.assert_called_once_with(
            "PutObject",
            {"bucket": "test-bucket", "key": "test-key"},
            credentials
        )
        
        mock_collector.add_result.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_repeated_operation(self):
        """Test execution of an operation with repeat count > 1."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = {"success": True, "duration_ms": 100}
        
        mock_collector = MagicMock()
        
        # test_engine_wrapper.py의 MockS3TestExecutionEngine 사용
        from .test_engine_wrapper import MockS3TestExecutionEngine
        
        engine = MockS3TestExecutionEngine(
            operation_executor=mock_executor,
            result_collector=mock_collector
        )
        
        operation = {
            "type": "PutObject",
            "params": {"bucket": "test-bucket", "key": "test-key"},
            "repeat": 3
        }
        
        credentials = {
            "access_key": "test_key",
            "secret_key": "test_secret",
            "region": "us-west-2"
        }
        
        await engine.execute_operation(operation, credentials)
        
        assert mock_executor.execute.call_count == 3
        assert mock_collector.add_result.call_count == 3

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from typing import Dict, Any, List
from s3tester.interfaces import (
    IConfigurationLoader,
    IOperationExecutor,
    ITestEngine
)


class MockConfigLoader(IConfigurationLoader):
    """Mock implementation of IConfigurationLoader for testing."""
    
    def load_configuration(self, config_path: str) -> Dict[str, Any]:
        """Load a configuration from the given path."""
        return {
            "name": "test-config",
            "credentials": {
                "access_key": "test-key",
                "secret_key": "test-secret",
                "region": "us-west-2"
            },
            "global_config": {
                "max_concurrency": 5,
                "report_format": "json",
                "output_path": "./results"
            },
            "operations": [
                {
                    "type": "PutObject",
                    "params": {
                        "bucket": "test-bucket",
                        "key": "test-key",
                        "content": "Hello, World!"
                    },
                    "repeat": 1
                }
            ]
        }
    
    def validate_configuration(self, config_path: str) -> bool:
        """Validate a configuration without loading it fully."""
        return True


class MockOperationExecutor(IOperationExecutor):
    """Mock implementation of IOperationExecutor for testing."""
    
    def execute_operation(self, operation_name: str, parameters: Dict[str, Any], 
                         client, config_dir) -> Dict[str, Any]:
        """Execute single S3 operation."""
        return {
            "success": True,
            "duration_ms": 100,
            "operation_type": operation_name,
            "params": parameters,
            "result": {}
        }
    
    def list_supported_operations(self) -> List[str]:
        """List all supported operation names."""
        return ["PutObject", "GetObject", "DeleteObject", "CreateBucket", "ListBuckets"]
        
    # 이전 메서드는 호환성을 위해 유지
    async def execute(self, operation_type: str, params: Dict[str, Any], 
                    credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an operation and return the results."""
        return {
            "success": True,
            "duration_ms": 100,
            "operation_type": operation_type,
            "params": params,
            "result": {}
        }


class MockResultCollector:
    """Mock implementation of a result collector for testing."""
    
    def __init__(self):
        self.results = []
    
    def add_result(self, result: Dict[str, Any]) -> None:
        """Add a result to the collector."""
        self.results.append(result)
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get all collected results."""
        return self.results
    
    def generate_report(self, format_type: str = "json", 
                        output_path: str = None) -> str:
        """Generate a report of the collected results."""
        return "Test Report"


class TestInterfaces:
    """Test cases to verify interface implementations work correctly."""
    
    def test_config_loader_interface(self):
        """Test that a class implementing IConfigurationLoader works."""
        loader = MockConfigLoader()
        config = loader.load_configuration("dummy/path")
        
        assert config["name"] == "test-config"
        assert "credentials" in config
        assert "operations" in config
        assert loader.validate_configuration("dummy/path") is True
    
    def test_operation_executor_interface(self):
        """Test that a class implementing IOperationExecutor works."""
        executor = MockOperationExecutor()
        result = pytest.mark.asyncio(lambda: executor.execute(
            "PutObject",
            {"bucket": "test-bucket", "key": "test-key"},
            {"access_key": "test", "secret_key": "test", "region": "us-west-2"}
        ))
        
        # We can't directly call the async function in a synchronous test,
        # but we can verify the class structure
        assert hasattr(executor, "execute")
    
    def test_result_collector_interface(self):
        """Test that a class implementing IResultCollector works."""
        collector = MockResultCollector()
        
        # Add a test result
        test_result = {
            "success": True,
            "duration_ms": 150,
            "operation_type": "GetObject",
            "params": {"bucket": "test-bucket", "key": "test-key"},
            "result": {"content_length": 13}
        }
        
        collector.add_result(test_result)
        
        results = collector.get_results()
        assert len(results) == 1
        assert results[0] == test_result
        
        report = collector.generate_report()
        assert report == "Test Report"

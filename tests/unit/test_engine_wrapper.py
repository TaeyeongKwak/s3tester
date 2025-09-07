"""
This module provides an interface to the S3TestExecutionEngine for unit tests.
"""

import asyncio
from typing import Dict, Any, Optional, List
from unittest.mock import MagicMock


class MockS3TestExecutionEngine:
    """Simplified implementation of S3TestExecutionEngine for unit tests."""
    
    def __init__(self, operation_executor=None, result_collector=None):
        """Initialize the engine."""
        self.operation_executor = operation_executor or MagicMock()
        self.result_collector = result_collector or MagicMock()
    
    async def execute_operation(self, operation: Dict[str, Any], credentials: Dict[str, Any]):
        """Execute a single operation."""
        # Extract operation type and parameters
        operation_type = operation["type"]
        params = operation["params"]
        repeat_count = operation.get("repeat", 1)
        
        # Execute the operation (potentially multiple times)
        for _ in range(repeat_count):
            result = self.operation_executor.execute(
                operation_type, params, credentials
            )
            self.result_collector.add_result(result)
        
        return True

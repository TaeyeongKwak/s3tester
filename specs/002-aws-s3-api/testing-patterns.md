# Testing Patterns and TDD Implementation Guide

## Test-Driven Development Workflow

### TDD Cycle Implementation

**RED-GREEN-REFACTOR Pattern for s3tester:**

1. **RED**: Write failing test first
2. **GREEN**: Implement minimal code to pass
3. **REFACTOR**: Improve code without changing behavior

### Git Commit Convention
```
feat: Add [component] - RED phase
test: Add [component] tests
feat: Implement [component] - GREEN phase  
refactor: Improve [component] implementation
```

## Contract Tests

### CLI Contract Tests

**File**: `tests/contract/test_cli_contract.py`

```python
import pytest
import subprocess
import json
import yaml
from pathlib import Path
from click.testing import CliRunner
from s3tester.cli import cli

class TestCLIContract:
    """Test CLI interface matches contract specification."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.test_config = Path("tests/fixtures/valid_config.yaml")
        self.ensure_test_config_exists()
    
    def ensure_test_config_exists(self):
        """Create test configuration if it doesn't exist."""
        if not self.test_config.exists():
            self.test_config.parent.mkdir(parents=True, exist_ok=True)
            test_config_content = {
                'config': {
                    'endpoint_url': 'http://localhost:9000',
                    'region': 'us-east-1',
                    'path_style': True,
                    'credentials': [{
                        'name': 'TestCred',
                        'access_key': 'test_key',
                        'secret_key': 'test_secret'
                    }]
                },
                'test_cases': {
                    'parallel': False,
                    'groups': [{
                        'name': 'Test Group',
                        'credential': 'TestCred',
                        'test': [{
                            'operation': 'ListBuckets',
                            'parameters': {},
                            'expected_result': {'success': True}
                        }]
                    }]
                }
            }
            with open(self.test_config, 'w') as f:
                yaml.dump(test_config_content, f)
    
    def test_help_command_shows_usage(self):
        """CLI shows help when invoked without arguments."""
        result = self.runner.invoke(cli, [])
        
        assert result.exit_code == 0
        assert "S3 API compatibility testing tool" in result.output
        assert "--config" in result.output
        assert "--dry-run" in result.output
        assert "--format" in result.output
    
    def test_version_command_shows_version(self):
        """CLI shows version information."""
        result = self.runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert "s3tester" in result.output
    
    def test_config_parameter_required_for_run(self):
        """Run command requires config parameter."""
        result = self.runner.invoke(cli, ['run'])
        
        assert result.exit_code == 2
        assert "Configuration file required" in result.output
    
    def test_validate_command_with_valid_config(self):
        """Validate command passes with valid configuration."""
        result = self.runner.invoke(cli, [
            '--config', str(self.test_config),
            'validate'
        ])
        
        # Should pass validation (exit code 0)
        assert result.exit_code == 0
        assert "Configuration is valid" in result.output
    
    def test_validate_command_with_nonexistent_config(self):
        """Validate command fails with non-existent config."""
        result = self.runner.invoke(cli, [
            '--config', 'nonexistent.yaml',
            'validate'
        ])
        
        assert result.exit_code == 2
    
    def test_list_operations_command(self):
        """List operations command shows supported operations."""
        result = self.runner.invoke(cli, ['list', 'operations'])
        
        assert result.exit_code == 0
        assert "Supported S3 Operations" in result.output
        assert "ListBuckets" in result.output
        assert "PutObject" in result.output
    
    def test_list_groups_command(self):
        """List groups command shows configured groups."""
        result = self.runner.invoke(cli, [
            '--config', str(self.test_config),
            'list', 'groups'
        ])
        
        assert result.exit_code == 0
        assert "Test Groups" in result.output
        assert "Test Group" in result.output
    
    def test_dry_run_flag(self):
        """Dry run flag validates without execution."""
        result = self.runner.invoke(cli, [
            '--config', str(self.test_config),
            '--dry-run',
            'run'
        ])
        
        # Should validate successfully but not execute
        assert result.exit_code == 0
    
    def test_output_formats(self):
        """Test different output formats."""
        for fmt in ['json', 'yaml', 'table']:
            result = self.runner.invoke(cli, [
                '--config', str(self.test_config),
                '--format', fmt,
                '--dry-run',
                'run'
            ])
            
            assert result.exit_code == 0, f"Format {fmt} failed"
    
    def test_parallel_execution_flag(self):
        """Test parallel execution option."""
        result = self.runner.invoke(cli, [
            '--config', str(self.test_config),
            '--dry-run',
            'run',
            '--parallel'
        ])
        
        assert result.exit_code == 0
    
    def test_group_filter(self):
        """Test group filtering option."""
        result = self.runner.invoke(cli, [
            '--config', str(self.test_config),
            '--dry-run',
            'run',
            '--group', 'Test Group'
        ])
        
        assert result.exit_code == 0
    
    def test_json_output_format_structure(self):
        """JSON output follows expected structure."""
        result = self.runner.invoke(cli, [
            '--config', str(self.test_config),
            '--format', 'json',
            '--dry-run',
            'run'
        ])
        
        assert result.exit_code == 0
        
        # Parse JSON output
        try:
            output_data = json.loads(result.output)
            
            # Verify required fields
            assert 'session_id' in output_data
            assert 'start_time' in output_data
            assert 'total_operations' in output_data
            assert 'summary' in output_data
            assert 'results' in output_data
            
            # Verify summary structure
            summary = output_data['summary']
            assert 'passed' in summary
            assert 'failed' in summary
            assert 'error' in summary
            assert 'success_rate' in summary
            
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

# Contract test for configuration schema
class TestConfigurationContract:
    """Test configuration follows JSON schema contract."""
    
    def test_configuration_schema_validation(self):
        """Valid configurations pass schema validation."""
        from s3tester.config.models import TestConfiguration
        
        valid_config = {
            'config': {
                'endpoint_url': 'https://s3.amazonaws.com',
                'region': 'us-east-1',
                'path_style': False,
                'credentials': [{
                    'name': 'TestCred',
                    'access_key': 'AKIATEST',
                    'secret_key': 'test_secret_key'
                }]
            },
            'test_cases': {
                'parallel': False,
                'groups': [{
                    'name': 'Basic Test',
                    'credential': 'TestCred',
                    'test': [{
                        'operation': 'ListBuckets',
                        'parameters': {},
                        'expected_result': {'success': True}
                    }]
                }]
            }
        }
        
        # Should not raise validation error
        config = TestConfiguration(**valid_config)
        assert config.config.endpoint_url == 'https://s3.amazonaws.com'
        assert len(config.test_cases.groups) == 1
    
    def test_invalid_configuration_fails_validation(self):
        """Invalid configurations fail validation."""
        from s3tester.config.models import TestConfiguration
        import pytest
        
        invalid_configs = [
            # Missing required fields
            {'config': {'endpoint_url': 'https://s3.amazonaws.com'}},
            # Invalid endpoint URL
            {'config': {'endpoint_url': 'not-a-url', 'region': 'us-east-1', 'credentials': []}},
            # Empty credentials
            {'config': {'endpoint_url': 'https://s3.amazonaws.com', 'region': 'us-east-1', 'credentials': []}}
        ]
        
        for invalid_config in invalid_configs:
            with pytest.raises(Exception):  # Pydantic ValidationError
                TestConfiguration(**invalid_config)
```

### Operation Contract Tests

**File**: `tests/contract/test_operations_contract.py`

```python
import pytest
from unittest.mock import Mock, MagicMock
from s3tester.operations.base import S3Operation, OperationContext, OperationResult
from s3tester.operations.registry import OperationRegistry
from pathlib import Path

class TestOperationContract:
    """Test all operations follow the base contract."""
    
    def test_all_operations_implement_required_methods(self):
        """All registered operations implement required interface."""
        for operation_name in OperationRegistry.list_operations():
            operation = OperationRegistry.get_operation(operation_name)
            
            # Check required methods exist
            assert hasattr(operation, 'validate_parameters')
            assert hasattr(operation, 'execute_operation')
            assert hasattr(operation, 'execute')
            
            # Check methods are callable
            assert callable(operation.validate_parameters)
            assert callable(operation.execute_operation)
            assert callable(operation.execute)
    
    def test_operation_parameter_validation(self):
        """Operations validate parameters correctly."""
        # Test with CreateBucket operation
        operation = OperationRegistry.get_operation("CreateBucket")
        
        # Valid parameters should not raise
        valid_params = {'bucket': 'test-bucket-123'}
        validated = operation.validate_parameters(valid_params)
        assert 'Bucket' in validated
        assert validated['Bucket'] == 'test-bucket-123'
        
        # Invalid parameters should raise ValueError
        with pytest.raises(ValueError, match="requires 'bucket' parameter"):
            operation.validate_parameters({})
        
        with pytest.raises(ValueError, match="Invalid bucket name"):
            operation.validate_parameters({'bucket': 'INVALID-BUCKET-NAME'})
    
    def test_operation_execution_result_format(self):
        """Operations return properly formatted results."""
        # Mock S3 client
        mock_client = Mock()
        mock_client.create_bucket.return_value = {
            'Location': '/test-bucket',
            'ResponseMetadata': {'HTTPStatusCode': 200}
        }
        
        # Create operation context
        context = OperationContext(
            s3_client=mock_client,
            operation_name="CreateBucket",
            parameters={'bucket': 'test-bucket'},
            config_dir=Path('/test'),
            dry_run=False
        )
        
        # Execute operation
        operation = OperationRegistry.get_operation("CreateBucket")
        result = operation.execute(context)
        
        # Verify result format
        assert isinstance(result, OperationResult)
        assert isinstance(result.success, bool)
        assert isinstance(result.duration, float)
        assert result.duration >= 0
        
        if result.success:
            assert result.response is not None
        else:
            assert result.error_code is not None or result.error_message is not None
    
    def test_dry_run_mode(self):
        """Operations respect dry-run mode."""
        mock_client = Mock()
        
        context = OperationContext(
            s3_client=mock_client,
            operation_name="CreateBucket",
            parameters={'bucket': 'test-bucket'},
            config_dir=Path('/test'),
            dry_run=True  # Enable dry run
        )
        
        operation = OperationRegistry.get_operation("CreateBucket")
        result = operation.execute(context)
        
        # In dry run, should succeed without calling S3
        assert result.success
        assert 'dry_run' in result.response
        assert not mock_client.create_bucket.called
    
    def test_file_reference_parameter_handling(self):
        """Operations handle file:// parameters correctly."""
        # Create temporary test file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_file = f.name
        
        try:
            operation = OperationRegistry.get_operation("PutObject")
            
            # Test file:// parameter
            params = {
                'bucket': 'test-bucket',
                'key': 'test-key',
                'body': f'file://{temp_file}'
            }
            
            validated = operation.validate_parameters(params)
            
            # Should transform file:// to actual content
            assert 'Body' in validated
            assert isinstance(validated['Body'], bytes)
            assert b'test content' in validated['Body']
            
        finally:
            os.unlink(temp_file)
```

### Integration Tests with Moto

**File**: `tests/integration/test_s3_operations_integration.py`

```python
import pytest
import boto3
from moto import mock_s3
from pathlib import Path
import tempfile
import os

from s3tester.config.models import TestConfiguration
from s3tester.core.engine import TestExecutionEngine
from s3tester.operations.registry import OperationRegistry

@mock_s3
class TestS3OperationsIntegration:
    """Integration tests using moto for S3 mocking."""
    
    def setup_method(self):
        """Set up S3 mock environment."""
        # Create mock S3 service
        self.s3_client = boto3.client(
            's3',
            region_name='us-east-1',
            aws_access_key_id='testing',
            aws_secret_access_key='testing'
        )
        
        # Create test bucket
        self.test_bucket = 'test-bucket-integration'
        self.s3_client.create_bucket(Bucket=self.test_bucket)
    
    def test_bucket_operations_integration(self):
        """Test bucket operations against mocked S3."""
        # Test ListBuckets
        response = self.s3_client.list_buckets()
        assert any(b['Name'] == self.test_bucket for b in response['Buckets'])
        
        # Test HeadBucket
        response = self.s3_client.head_bucket(Bucket=self.test_bucket)
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200
        
        # Test bucket operations through our operation system
        from s3tester.operations.base import OperationContext
        
        # Test CreateBucket operation
        create_bucket_op = OperationRegistry.get_operation("CreateBucket")
        context = OperationContext(
            s3_client=self.s3_client,
            operation_name="CreateBucket",
            parameters={'bucket': 'new-test-bucket'},
            config_dir=Path('/test')
        )
        
        result = create_bucket_op.execute(context)
        assert result.success
        
        # Verify bucket was created
        response = self.s3_client.list_buckets()
        bucket_names = [b['Name'] for b in response['Buckets']]
        assert 'new-test-bucket' in bucket_names
    
    def test_object_operations_integration(self):
        """Test object operations against mocked S3."""
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("integration test content")
            temp_file = Path(f.name)
        
        try:
            # Test PutObject operation
            put_object_op = OperationRegistry.get_operation("PutObject")
            context = OperationContext(
                s3_client=self.s3_client,
                operation_name="PutObject",
                parameters={
                    'bucket': self.test_bucket,
                    'key': 'test-object',
                    'body': f'file://{temp_file}'
                },
                config_dir=temp_file.parent
            )
            
            result = put_object_op.execute(context)
            assert result.success
            assert 'ETag' in result.response
            
            # Verify object exists
            objects = self.s3_client.list_objects_v2(Bucket=self.test_bucket)
            assert 'Contents' in objects
            assert any(obj['Key'] == 'test-object' for obj in objects['Contents'])
            
            # Test GetObject operation
            get_object_op = OperationRegistry.get_operation("GetObject")
            context = OperationContext(
                s3_client=self.s3_client,
                operation_name="GetObject",
                parameters={
                    'bucket': self.test_bucket,
                    'key': 'test-object'
                },
                config_dir=Path('/test')
            )
            
            result = get_object_op.execute(context)
            assert result.success
            assert b'integration test content' in result.response['Body']
            
        finally:
            os.unlink(temp_file)
    
    def test_error_handling_integration(self):
        """Test error handling with mocked S3 errors."""
        # Test operation on non-existent bucket
        get_object_op = OperationRegistry.get_operation("GetObject")
        context = OperationContext(
            s3_client=self.s3_client,
            operation_name="GetObject",
            parameters={
                'bucket': 'nonexistent-bucket',
                'key': 'test-object'
            },
            config_dir=Path('/test')
        )
        
        result = get_object_op.execute(context)
        assert not result.success
        assert result.error_code == 'NoSuchBucket'
        
        # Test operation on non-existent object
        context = OperationContext(
            s3_client=self.s3_client,
            operation_name="GetObject",
            parameters={
                'bucket': self.test_bucket,
                'key': 'nonexistent-object'
            },
            config_dir=Path('/test')
        )
        
        result = get_object_op.execute(context)
        assert not result.success
        assert result.error_code == 'NoSuchKey'

@mock_s3  
class TestEngineIntegration:
    """Integration tests for the execution engine."""
    
    def create_test_configuration(self) -> TestConfiguration:
        """Create test configuration for integration tests."""
        config_dict = {
            'config': {
                'endpoint_url': 'https://s3.amazonaws.com',
                'region': 'us-east-1',
                'path_style': False,
                'credentials': [{
                    'name': 'TestCred',
                    'access_key': 'testing',
                    'secret_key': 'testing'
                }]
            },
            'test_cases': {
                'parallel': False,
                'groups': [{
                    'name': 'Integration Test Group',
                    'credential': 'TestCred',
                    'before_test': [{
                        'operation': 'CreateBucket',
                        'parameters': {'bucket': 'integration-test-bucket'},
                        'expected_result': {'success': True}
                    }],
                    'test': [{
                        'operation': 'ListBuckets',
                        'parameters': {},
                        'expected_result': {'success': True}
                    }, {
                        'operation': 'HeadBucket',
                        'parameters': {'bucket': 'integration-test-bucket'},
                        'expected_result': {'success': True}
                    }],
                    'after_test': [{
                        'operation': 'DeleteBucket',
                        'parameters': {'bucket': 'integration-test-bucket'},
                        'expected_result': {'success': True}
                    }]
                }]
            }
        }
        
        return TestConfiguration(**config_dict)
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self):
        """Test complete workflow from configuration to results."""
        import asyncio
        
        # Create test configuration
        config = self.create_test_configuration()
        
        # Create engine
        engine = TestExecutionEngine(config, dry_run=False)
        
        # Execute tests
        session = await engine.execute_tests()
        
        # Verify results
        assert session.total_operations == 4  # 1 before + 2 test + 1 after
        assert session.summary.passed >= 3  # At least before + test operations should pass
        assert session.summary.error == 0  # No errors expected
        
        # Verify all operations were executed
        operation_names = [result.operation_name for result in session.results]
        expected_operations = ['CreateBucket', 'ListBuckets', 'HeadBucket', 'DeleteBucket']
        
        for expected_op in expected_operations:
            assert expected_op in operation_names
        
        # Verify group execution flow
        group_results = [r for r in session.results if r.group_name == 'Integration Test Group']
        assert len(group_results) == 4
    
    @pytest.mark.asyncio
    async def test_parallel_execution_integration(self):
        """Test parallel execution mode."""
        config = self.create_test_configuration()
        config.test_cases.parallel = True
        
        engine = TestExecutionEngine(config, dry_run=False)
        session = await engine.execute_tests()
        
        # Should complete successfully even in parallel mode
        assert session.summary.error == 0
        assert session.total_operations == 4
```

### Performance Tests

**File**: `tests/integration/test_performance.py`

```python
import pytest
import time
import asyncio
from s3tester.config.models import TestConfiguration
from s3tester.core.engine import TestExecutionEngine

class TestPerformance:
    """Performance tests for s3tester."""
    
    def create_large_test_configuration(self, num_operations: int) -> TestConfiguration:
        """Create configuration with many operations for performance testing."""
        operations = []
        for i in range(num_operations):
            operations.append({
                'operation': 'ListBuckets',
                'parameters': {},
                'expected_result': {'success': True}
            })
        
        config_dict = {
            'config': {
                'endpoint_url': 'https://s3.amazonaws.com',
                'region': 'us-east-1',
                'path_style': False,
                'credentials': [{
                    'name': 'TestCred',
                    'access_key': 'testing',
                    'secret_key': 'testing'
                }]
            },
            'test_cases': {
                'parallel': True,  # Use parallel for performance
                'groups': [{
                    'name': 'Performance Test Group',
                    'credential': 'TestCred',
                    'test': operations
                }]
            }
        }
        
        return TestConfiguration(**config_dict)
    
    @pytest.mark.asyncio
    @pytest.mark.slow  # Mark as slow test
    async def test_concurrent_operations_performance(self):
        """Test performance with concurrent operations."""
        num_operations = 50
        config = self.create_large_test_configuration(num_operations)
        
        engine = TestExecutionEngine(config, dry_run=True)  # Use dry run for speed
        
        start_time = time.time()
        session = await engine.execute_tests()
        duration = time.time() - start_time
        
        # Verify all operations completed
        assert session.total_operations == num_operations
        assert session.summary.passed == num_operations
        
        # Performance assertions
        assert duration < 10.0  # Should complete in under 10 seconds
        ops_per_second = num_operations / duration
        assert ops_per_second > 10  # Should handle at least 10 ops/second
        
        print(f"Performance: {num_operations} operations in {duration:.2f}s ({ops_per_second:.1f} ops/sec)")
    
    @pytest.mark.asyncio
    def test_memory_usage_stability(self):
        """Test that memory usage remains stable during execution."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Execute multiple test runs
        config = self.create_large_test_configuration(20)
        engine = TestExecutionEngine(config, dry_run=True)
        
        for i in range(5):
            session = asyncio.run(engine.execute_tests())
            assert session.total_operations == 20
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be minimal (less than 10MB)
        assert memory_growth < 10 * 1024 * 1024, f"Memory grew by {memory_growth / 1024 / 1024:.1f}MB"
```

### Unit Test Examples

**File**: `tests/unit/test_data_models.py`

```python
import pytest
from pathlib import Path
from s3tester.config.models import TestConfiguration, CredentialSet, TestGroup

class TestDataModels:
    """Unit tests for data models."""
    
    def test_credential_set_validation(self):
        """Test credential set validation rules."""
        # Valid credential set
        cred = CredentialSet(
            name="TestCred",
            access_key="AKIATEST",
            secret_key="test_secret"
        )
        assert cred.name == "TestCred"
        
        # Test boto3 credentials conversion
        boto_creds = cred.to_boto3_credentials()
        assert 'aws_access_key_id' in boto_creds
        assert 'aws_secret_access_key' in boto_creds
        assert boto_creds['aws_access_key_id'] == "AKIATEST"
        
        # Invalid name characters
        with pytest.raises(ValueError, match="invalid characters"):
            CredentialSet(
                name="Test Cred With Spaces",
                access_key="AKIATEST",
                secret_key="test_secret"
            )
    
    def test_test_group_status_transitions(self):
        """Test test group status state machine."""
        from s3tester.config.models import TestGroupStatus, Operation, ExpectedResult
        
        # Create test group
        group = TestGroup(
            name="Test Group",
            credential="TestCred",
            test=[Operation(
                operation="ListBuckets",
                parameters={},
                expected_result=ExpectedResult(success=True)
            )]
        )
        
        # Initial state
        assert group._status == TestGroupStatus.PENDING
        assert group.duration is None
        
        # Transition to running
        group.set_status(TestGroupStatus.RUNNING_BEFORE)
        assert group._status == TestGroupStatus.RUNNING_BEFORE
        assert group._start_time is not None
        
        # Complete execution
        group.set_status(TestGroupStatus.COMPLETED)
        assert group._status == TestGroupStatus.COMPLETED
        assert group._end_time is not None
        assert group.duration is not None
        assert group.duration > 0
    
    def test_file_reference_resolution(self):
        """Test file reference path resolution."""
        from s3tester.config.models import FileReference
        import tempfile
        
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_file = Path(f.name)
        
        try:
            # Test file:// URL resolution
            base_dir = temp_file.parent
            file_ref = FileReference.from_path_spec(f"file://./{temp_file.name}", base_dir)
            
            assert file_ref.exists
            assert file_ref.resolved_path.exists()
            assert file_ref.read_text() == "test content"
            
            # Test relative path resolution
            file_ref2 = FileReference.from_path_spec(f"./{temp_file.name}", base_dir)
            assert file_ref2.exists
            
        finally:
            temp_file.unlink()
```

## TDD Implementation Checklist

### For Each Component:

1. **RED Phase**:
   ```python
   def test_component_behavior():
       # Test fails because component doesn't exist
       assert False, "Component not implemented"
   ```

2. **GREEN Phase**:
   ```python
   def component_minimal_implementation():
       # Minimal code to make test pass
       return "placeholder"
   ```

3. **REFACTOR Phase**:
   ```python
   def component_improved_implementation():
       # Clean, maintainable implementation
       return actual_logic()
   ```

### Test Organization:

- **Contract Tests**: Verify interfaces match specifications
- **Unit Tests**: Test individual components in isolation  
- **Integration Tests**: Test component interactions with moto
- **Performance Tests**: Validate performance requirements
- **End-to-End Tests**: Test complete workflows

### Continuous Integration:

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-asyncio moto[s3]
      
      - name: Run contract tests
        run: pytest tests/contract/ -v
      
      - name: Run unit tests  
        run: pytest tests/unit/ -v
      
      - name: Run integration tests
        run: pytest tests/integration/ -v
      
      - name: Run performance tests
        run: pytest tests/integration/test_performance.py -m "not slow" -v
```

## Testing Best Practices

1. **Test Isolation**: Each test is independent and can run alone
2. **Real Dependencies**: Use moto for S3, avoid mocking internal components  
3. **Clear Assertions**: Test one thing at a time with descriptive failures
4. **Fast Execution**: Keep unit tests under 100ms, integration tests under 1s
5. **Comprehensive Coverage**: Test happy path, error cases, and edge conditions
6. **Documentation**: Tests serve as examples and documentation

The testing patterns ensure constitutional compliance with TDD requirements while providing comprehensive test coverage for reliable S3 API testing functionality.
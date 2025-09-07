# Core Execution Engine Implementation Guide

## Engine Architecture Overview

### Test Execution Orchestrator

**File**: `src/s3tester/core/engine.py`

```python
import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import boto3
from botocore.config import Config

from ..config.models import (
    TestConfiguration, TestGroup, Operation, TestSession, 
    TestResult, TestGroupStatus, TestResultStatus
)
from ..operations.registry import OperationRegistry
from ..operations.base import OperationContext
from .client_factory import S3ClientFactory
from .result_collector import ResultCollector

class TestExecutionEngine:
    """Core engine for executing S3 test scenarios."""
    
    def __init__(self, config: TestConfiguration, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.logger = logging.getLogger("s3tester.engine")
        
        # Initialize components
        self.client_factory = S3ClientFactory(config.config)
        self.result_collector = ResultCollector()
        
        # Execution state
        self.session: Optional[TestSession] = None
        self._cancelled = False
        
    async def execute_tests(self, 
                          group_names: Optional[List[str]] = None,
                          parallel: Optional[bool] = None) -> TestSession:
        """Execute test scenarios and return results."""
        
        # Initialize test session
        session_id = str(uuid.uuid4())
        self.session = TestSession(
            session_id=session_id,
            config_file=self.config._config_file_path or Path("unknown"),
            start_time=datetime.utcnow()
        )
        
        self.logger.info(f"Starting test session {session_id}")
        
        try:
            # Filter test groups if specified
            groups_to_execute = self._filter_groups(group_names)
            
            # Determine execution mode
            execute_parallel = parallel if parallel is not None else self.config.test_cases.parallel
            
            # Execute test groups
            if execute_parallel:
                await self._execute_groups_parallel(groups_to_execute)
            else:
                await self._execute_groups_sequential(groups_to_execute)
                
            # Finalize session
            self.session.finalize()
            
            self.logger.info(
                f"Test session completed: {self.session.summary.passed} passed, "
                f"{self.session.summary.failed} failed, {self.session.summary.error} errors"
            )
            
            return self.session
            
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            if self.session:
                self.session.finalize()
            raise
    
    def _filter_groups(self, group_names: Optional[List[str]]) -> List[TestGroup]:
        """Filter test groups by name."""
        all_groups = self.config.test_cases.groups
        
        if not group_names:
            return all_groups
        
        filtered_groups = []
        for name in group_names:
            group = self.config.test_cases.get_group(name)
            if not group:
                raise ValueError(f"Test group not found: {name}")
            filtered_groups.append(group)
        
        return filtered_groups
    
    async def _execute_groups_parallel(self, groups: List[TestGroup]):
        """Execute test groups in parallel."""
        self.logger.info(f"Executing {len(groups)} groups in parallel")
        
        # Create tasks for each group
        tasks = []
        for group in groups:
            task = asyncio.create_task(self._execute_group(group))
            tasks.append(task)
        
        # Wait for all groups to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_groups_sequential(self, groups: List[TestGroup]):
        """Execute test groups sequentially."""
        self.logger.info(f"Executing {len(groups)} groups sequentially")
        
        for group in groups:
            if self._cancelled:
                break
            await self._execute_group(group)
    
    async def _execute_group(self, group: TestGroup):
        """Execute a single test group with before/test/after phases."""
        group_logger = logging.getLogger(f"s3tester.engine.{group.name}")
        group_logger.info(f"Starting test group: {group.name}")
        
        # Update group status
        group.set_status(TestGroupStatus.RUNNING_BEFORE)
        
        try:
            # Get S3 client for this group
            client = self._get_client_for_group(group)
            
            # Phase 1: Before test operations
            if group.before_test:
                group_logger.info(f"Executing {len(group.before_test)} before-test operations")
                before_success = await self._execute_operations(
                    group.before_test, group, client, "before"
                )
                
                if not before_success:
                    group.set_status(TestGroupStatus.FAILED)
                    group_logger.error("Before-test operations failed, skipping test and after-test")
                    return
            
            # Phase 2: Test operations
            group.set_status(TestGroupStatus.RUNNING_TEST)
            group_logger.info(f"Executing {len(group.test)} test operations")
            await self._execute_operations(group.test, group, client, "test")
            
            # Phase 3: After test operations (cleanup)
            if group.after_test:
                group.set_status(TestGroupStatus.RUNNING_AFTER)
                group_logger.info(f"Executing {len(group.after_test)} after-test operations")
                await self._execute_operations(group.after_test, group, client, "after")
            
            group.set_status(TestGroupStatus.COMPLETED)
            group_logger.info(f"Test group completed in {group.duration:.2f}s")
            
        except Exception as e:
            group.set_status(TestGroupStatus.FAILED)
            group_logger.error(f"Test group failed: {e}")
            raise
    
    def _get_client_for_group(self, group: TestGroup) -> boto3.client:
        """Get S3 client for test group."""
        credential_name = group.credential
        credential = self.config.config.get_credential(credential_name)
        
        if not credential:
            raise ValueError(f"Credential not found: {credential_name}")
        
        return self.client_factory.create_client(credential)
    
    async def _execute_operations(self, 
                                operations: List[Operation],
                                group: TestGroup,
                                default_client: boto3.client,
                                phase: str) -> bool:
        """Execute a list of operations."""
        if not operations:
            return True
        
        # For before-test operations, fail fast
        # For test operations, continue on failure
        # For after-test operations, continue on failure (cleanup)
        fail_fast = (phase == "before")
        
        success_count = 0
        
        # Use ThreadPoolExecutor for concurrent S3 operations
        max_workers = min(10, len(operations))  # Reasonable concurrency limit
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            loop = asyncio.get_event_loop()
            
            # Create tasks for all operations
            tasks = []
            for operation in operations:
                task = loop.run_in_executor(
                    executor,
                    self._execute_single_operation,
                    operation, group, default_client, phase
                )
                tasks.append(task)
            
            # Wait for all operations
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Operation {operations[i].operation} failed: {result}")
                    if fail_fast:
                        return False
                elif result:  # Successful operation
                    success_count += 1
                elif fail_fast:
                    return False
        
        return success_count > 0 if fail_fast else True
    
    def _execute_single_operation(self, 
                                operation: Operation,
                                group: TestGroup,
                                default_client: boto3.client,
                                phase: str) -> bool:
        """Execute a single operation (runs in thread pool)."""
        
        # Get client (use override if specified)
        client = default_client
        if operation.credential:
            credential = self.config.config.get_credential(operation.credential)
            if credential:
                client = self.client_factory.create_client(credential)
        
        # Resolve file paths relative to config directory
        resolved_operation = operation.resolve_file_paths(
            self.config._config_file_path.parent if self.config._config_file_path else Path.cwd()
        )
        
        # Create operation context
        context = OperationContext(
            s3_client=client,
            operation_name=operation.operation,
            parameters=resolved_operation.parameters,
            config_dir=self.config._config_file_path.parent if self.config._config_file_path else Path.cwd(),
            dry_run=self.dry_run
        )
        
        # Get operation implementation
        op_impl = OperationRegistry.get_operation(operation.operation)
        
        # Execute operation
        op_result = op_impl.execute(context)
        
        # Create test result
        test_result = TestResult(
            operation_name=operation.operation,
            group_name=group.name,
            expected=operation.expected_result
        )
        
        # Update result based on execution
        test_result.set_result(
            success=op_result.success,
            duration=op_result.duration,
            actual_response=op_result.response,
            error_message=op_result.error_message
        )
        
        # Add to session results
        if self.session:
            self.session.add_result(test_result)
        
        # Log result
        status_emoji = "✅" if test_result.status == TestResultStatus.PASS else "❌"
        self.logger.info(
            f"{status_emoji} {group.name} > {operation.operation} "
            f"({test_result.status.value}) [{test_result.duration:.2f}s]"
        )
        
        if test_result.error_message:
            self.logger.debug(f"Error details: {test_result.error_message}")
        
        return test_result.status == TestResultStatus.PASS
    
    def cancel(self):
        """Cancel test execution."""
        self._cancelled = True
        self.logger.info("Test execution cancellation requested")
```

### S3 Client Factory

**File**: `src/s3tester/core/client_factory.py`

```python
import boto3
from botocore.config import Config
from typing import Dict
from ..config.models import GlobalConfig, CredentialSet
import logging

class S3ClientFactory:
    """Factory for creating configured S3 clients."""
    
    def __init__(self, global_config: GlobalConfig):
        self.global_config = global_config
        self.logger = logging.getLogger("s3tester.client_factory")
        
        # Client cache for reuse
        self._client_cache: Dict[str, boto3.client] = {}
        
        # Base boto3 configuration
        self.boto_config = Config(
            retries={
                'total_max_attempts': 5,
                'mode': 'standard'
            },
            max_pool_connections=50,  # For high concurrency
            read_timeout=300,  # 5 minutes
            connect_timeout=30  # 30 seconds
        )
    
    def create_client(self, credential: CredentialSet) -> boto3.client:
        """Create S3 client with specified credentials."""
        cache_key = self._get_cache_key(credential)
        
        if cache_key in self._client_cache:
            return self._client_cache[cache_key]
        
        # Create boto3 session with credentials
        session = boto3.Session(**credential.to_boto3_credentials())
        
        # Create S3 client
        client_kwargs = {
            'service_name': 's3',
            'region_name': self.global_config.region,
            'endpoint_url': self.global_config.endpoint_url,
            'config': self.boto_config
        }
        
        # Handle path-style addressing
        if self.global_config.path_style:
            client_kwargs['config'] = self.boto_config.merge(
                Config(s3={'addressing_style': 'path'})
            )
        
        client = session.client(**client_kwargs)
        
        # Cache client for reuse
        self._client_cache[cache_key] = client
        
        self.logger.debug(
            f"Created S3 client for {credential.name} -> {self.global_config.endpoint_url}"
        )
        
        return client
    
    def _get_cache_key(self, credential: CredentialSet) -> str:
        """Generate cache key for credential set."""
        return f"{credential.name}:{credential.access_key[:8]}"
    
    def clear_cache(self):
        """Clear client cache."""
        self._client_cache.clear()
        self.logger.debug("S3 client cache cleared")
    
    def test_client_connection(self, credential: CredentialSet) -> bool:
        """Test client connection with simple operation."""
        try:
            client = self.create_client(credential)
            
            # Try a simple operation that doesn't require specific permissions
            client.list_buckets()
            return True
            
        except Exception as e:
            self.logger.error(f"Client connection test failed for {credential.name}: {e}")
            return False
```

### Result Collector

**File**: `src/s3tester/core/result_collector.py`

```python
from typing import List, Dict, Any
from collections import defaultdict
from ..config.models import TestResult, TestResultStatus, TestSummary
import logging

class ResultCollector:
    """Collect and aggregate test results."""
    
    def __init__(self):
        self.logger = logging.getLogger("s3tester.result_collector")
        
    def aggregate_by_group(self, results: List[TestResult]) -> Dict[str, Dict[str, Any]]:
        """Aggregate results by test group."""
        group_stats = defaultdict(lambda: {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'error': 0,
            'duration': 0.0,
            'operations': []
        })
        
        for result in results:
            group_name = result.group_name
            stats = group_stats[group_name]
            
            stats['total'] += 1
            stats['duration'] += result.duration
            stats['operations'].append(result)
            
            if result.status == TestResultStatus.PASS:
                stats['passed'] += 1
            elif result.status == TestResultStatus.FAIL:
                stats['failed'] += 1
            elif result.status == TestResultStatus.ERROR:
                stats['error'] += 1
        
        # Calculate success rates
        for group_name, stats in group_stats.items():
            if stats['total'] > 0:
                stats['success_rate'] = stats['passed'] / stats['total']
            else:
                stats['success_rate'] = 0.0
        
        return dict(group_stats)
    
    def get_failed_operations(self, results: List[TestResult]) -> List[TestResult]:
        """Get list of failed operations for reporting."""
        return [
            result for result in results 
            if result.status in [TestResultStatus.FAIL, TestResultStatus.ERROR]
        ]
    
    def get_performance_stats(self, results: List[TestResult]) -> Dict[str, float]:
        """Calculate performance statistics."""
        if not results:
            return {}
        
        durations = [result.duration for result in results]
        durations.sort()
        
        total_duration = sum(durations)
        count = len(durations)
        
        stats = {
            'total_duration': total_duration,
            'average_duration': total_duration / count,
            'min_duration': durations[0],
            'max_duration': durations[-1],
            'operations_per_second': count / total_duration if total_duration > 0 else 0
        }
        
        # Percentiles
        if count >= 2:
            stats['p50_duration'] = durations[int(count * 0.5)]
            stats['p90_duration'] = durations[int(count * 0.9)]
            stats['p95_duration'] = durations[int(count * 0.95)]
        
        return stats
    
    def generate_failure_report(self, results: List[TestResult]) -> str:
        """Generate detailed failure report."""
        failed_results = self.get_failed_operations(results)
        
        if not failed_results:
            return "No failures to report."
        
        report_lines = [f"Failure Report ({len(failed_results)} failures):"]
        report_lines.append("")
        
        for result in failed_results:
            report_lines.append(f"❌ {result.group_name} > {result.operation_name}")
            
            if result.error_message:
                report_lines.append(f"   Error: {result.error_message}")
            
            if result.expected.success and not result.success:
                report_lines.append("   Expected: Success")
                report_lines.append("   Actual: Failure")
            elif not result.expected.success and result.expected.error_code:
                expected_error = result.expected.error_code
                actual_error = result.actual.get('Error', {}).get('Code', 'Unknown') if result.actual else 'Unknown'
                report_lines.append(f"   Expected Error: {expected_error}")
                report_lines.append(f"   Actual Error: {actual_error}")
            
            report_lines.append(f"   Duration: {result.duration:.2f}s")
            report_lines.append("")
        
        return "\n".join(report_lines)
```

### Progress Tracking

**File**: `src/s3tester/core/progress.py`

```python
from typing import Optional, Callable
from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeElapsedColumn
from rich.console import Console
import logging

class TestProgressTracker:
    """Track and display test execution progress."""
    
    def __init__(self, console: Optional[Console] = None, show_progress: bool = True):
        self.console = console or Console()
        self.show_progress = show_progress
        self.logger = logging.getLogger("s3tester.progress")
        
        self.progress: Optional[Progress] = None
        self.main_task: Optional[TaskID] = None
        self.group_task: Optional[TaskID] = None
        
    def start_session(self, total_groups: int, total_operations: int):
        """Start tracking session progress."""
        if not self.show_progress:
            return
        
        self.progress = Progress(
            TextColumn("[bold blue]{task.fields[name]}", justify="left"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            TextColumn("{task.completed}/{task.total}"),
            "•",
            TimeElapsedColumn(),
            console=self.console,
            expand=True
        )
        
        self.progress.start()
        
        # Create main progress task
        self.main_task = self.progress.add_task(
            "Overall Progress",
            total=total_operations,
            name="Overall Progress"
        )
        
        self.logger.info(f"Started progress tracking: {total_groups} groups, {total_operations} operations")
    
    def start_group(self, group_name: str, operations_count: int):
        """Start tracking group progress."""
        if not self.progress:
            return
        
        if self.group_task:
            self.progress.remove_task(self.group_task)
        
        self.group_task = self.progress.add_task(
            group_name,
            total=operations_count,
            name=f"Group: {group_name}"
        )
    
    def update_operation(self, operation_name: str, success: bool):
        """Update progress for completed operation."""
        if not self.progress:
            return
        
        # Update main task
        if self.main_task:
            self.progress.update(self.main_task, advance=1)
        
        # Update group task
        if self.group_task:
            self.progress.update(self.group_task, advance=1)
        
        # Log operation result
        status = "✅" if success else "❌"
        self.logger.debug(f"{status} {operation_name}")
    
    def finish_group(self, group_name: str):
        """Finish group progress tracking."""
        if not self.progress or not self.group_task:
            return
        
        self.progress.update(self.group_task, completed=True)
        self.logger.info(f"Completed group: {group_name}")
    
    def finish_session(self):
        """Finish session progress tracking."""
        if not self.progress:
            return
        
        if self.main_task:
            self.progress.update(self.main_task, completed=True)
        
        self.progress.stop()
        self.logger.info("Progress tracking completed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.progress:
            self.progress.stop()
```

### Configuration Validator

**File**: `src/s3tester/core/validator.py`

```python
from typing import List, Dict, Any, Tuple
from pathlib import Path
from ..config.models import TestConfiguration
from ..operations.registry import OperationRegistry
import logging

class ConfigurationValidator:
    """Validate test configuration comprehensively."""
    
    def __init__(self):
        self.logger = logging.getLogger("s3tester.validator")
        
    def validate_configuration(self, 
                             config: TestConfiguration, 
                             strict: bool = False) -> Tuple[bool, List[str]]:
        """Validate configuration and return (is_valid, error_messages)."""
        errors = []
        
        # Basic structural validation (already done by Pydantic)
        
        # Validate credential references
        errors.extend(self._validate_credential_references(config))
        
        # Validate operations
        errors.extend(self._validate_operations(config))
        
        # Validate file references (if strict mode)
        if strict:
            errors.extend(self._validate_file_references(config))
        
        # Validate S3 connectivity (if strict mode)
        if strict:
            errors.extend(self._validate_s3_connectivity(config))
        
        is_valid = len(errors) == 0
        
        if is_valid:
            self.logger.info("Configuration validation passed")
        else:
            self.logger.error(f"Configuration validation failed with {len(errors)} errors")
            for error in errors:
                self.logger.error(f"  - {error}")
        
        return is_valid, errors
    
    def _validate_credential_references(self, config: TestConfiguration) -> List[str]:
        """Validate all credential references exist."""
        errors = []
        credential_names = {cred.name for cred in config.config.credentials}
        
        # Check group credential references
        for group in config.test_cases.groups:
            if group.credential not in credential_names:
                errors.append(f"Group '{group.name}' references unknown credential '{group.credential}'")
        
        # Check operation credential overrides
        for group in config.test_cases.groups:
            for phase, operations in [
                ("before_test", group.before_test),
                ("test", group.test),
                ("after_test", group.after_test)
            ]:
                for op in operations:
                    if op.credential and op.credential not in credential_names:
                        errors.append(
                            f"Operation '{op.operation}' in group '{group.name}' "
                            f"references unknown credential '{op.credential}'"
                        )
        
        return errors
    
    def _validate_operations(self, config: TestConfiguration) -> List[str]:
        """Validate all operations are supported."""
        errors = []
        supported_ops = set(OperationRegistry.list_operations())
        
        for group in config.test_cases.groups:
            for phase, operations in [
                ("before_test", group.before_test),
                ("test", group.test),
                ("after_test", group.after_test)
            ]:
                for op in operations:
                    if op.operation not in supported_ops:
                        errors.append(
                            f"Unsupported operation '{op.operation}' in group '{group.name}'"
                        )
        
        return errors
    
    def _validate_file_references(self, config: TestConfiguration) -> List[str]:
        """Validate all file:// references exist."""
        errors = []
        config_dir = config._config_file_path.parent if config._config_file_path else Path.cwd()
        
        for group in config.test_cases.groups:
            for phase, operations in [
                ("before_test", group.before_test),
                ("test", group.test),
                ("after_test", group.after_test)
            ]:
                for op in operations:
                    for param_name, param_value in op.parameters.items():
                        if isinstance(param_value, str) and param_value.startswith('file://'):
                            try:
                                from ..config.models import FileReference
                                file_ref = FileReference.from_path_spec(param_value, config_dir)
                                if not file_ref.exists:
                                    errors.append(
                                        f"File not found: {file_ref.resolved_path} "
                                        f"(referenced in {group.name}:{op.operation}:{param_name})"
                                    )
                            except Exception as e:
                                errors.append(
                                    f"Invalid file reference '{param_value}' "
                                    f"in {group.name}:{op.operation}:{param_name}: {e}"
                                )
        
        return errors
    
    def _validate_s3_connectivity(self, config: TestConfiguration) -> List[str]:
        """Test S3 connectivity for all credentials."""
        errors = []
        
        from .client_factory import S3ClientFactory
        client_factory = S3ClientFactory(config.config)
        
        for credential in config.config.credentials:
            try:
                if not client_factory.test_client_connection(credential):
                    errors.append(f"Cannot connect to S3 with credential '{credential.name}'")
            except Exception as e:
                errors.append(f"S3 connectivity test failed for '{credential.name}': {e}")
        
        return errors
```

## Usage Examples

### Basic Engine Usage
```python
from pathlib import Path
from s3tester.config.models import TestConfiguration
from s3tester.core.engine import TestExecutionEngine
import asyncio

# Load configuration
config_path = Path("test-config.yaml")
config = TestConfiguration.load_from_file(config_path)

# Create and run engine
engine = TestExecutionEngine(config, dry_run=False)
session = asyncio.run(engine.execute_tests())

print(f"Results: {session.summary.passed} passed, {session.summary.failed} failed")
```

### With Progress Tracking
```python
from s3tester.core.progress import TestProgressTracker
from rich.console import Console

console = Console()
with TestProgressTracker(console) as progress:
    engine = TestExecutionEngine(config)
    # Progress tracking would be integrated into engine execution
    session = asyncio.run(engine.execute_tests())
```

### Configuration Validation
```python
from s3tester.core.validator import ConfigurationValidator

validator = ConfigurationValidator()
is_valid, errors = validator.validate_configuration(config, strict=True)

if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

## Integration Points

### With CLI Layer
- Engine receives configuration from CLI argument parsing
- Progress display can be controlled by CLI verbosity flags
- Results are returned to CLI for formatting and output

### With Operations Layer
- Engine uses OperationRegistry to get operation implementations
- Passes OperationContext to each operation
- Collects OperationResult from each execution

### With Configuration Layer
- Engine loads TestConfiguration with full validation
- Handles file path resolution relative to config directory
- Manages credential references and client creation

## Performance Considerations

1. **Concurrency Control**: ThreadPoolExecutor with reasonable limits (10 workers)
2. **Client Reuse**: S3ClientFactory caches clients by credential
3. **Memory Management**: Results are collected incrementally
4. **Error Isolation**: Individual operation failures don't stop test execution
5. **Progress Tracking**: Optional to reduce overhead in automated environments

## Next Steps

The core engine provides:
1. **CLI Integration**: Ready for command-line interface integration
2. **Result Reporting**: Structured results for multiple output formats
3. **Configuration Validation**: Comprehensive validation with detailed errors
4. **Performance Monitoring**: Built-in timing and progress tracking
5. **Error Handling**: Robust error isolation and reporting
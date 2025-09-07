import asyncio
import os
import uuid
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import boto3

from ..config.models import (
    S3TestConfiguration, S3TestGroup, Operation, S3TestSession, 
    S3TestResult, S3TestGroupStatus, S3TestResultStatus
)
from ..operations.registry import OperationRegistry
from ..operations.base import OperationContext
from .client_factory import S3ClientFactory
from .result_collector import ResultCollector
from .logging_config import get_logger, log_operation_start, log_operation_success, log_operation_error

class S3TestExecutionEngine:
    """Core engine for executing S3 test scenarios.
    
    This class orchestrates the execution of S3 API compatibility tests,
    managing test sessions, parallel execution, and result collection.
    
    Attributes:
        config: Test configuration containing scenarios and settings
        dry_run: If True, operations are simulated without actual API calls
        logger: Structured logger for operation tracking
        client_factory: Factory for creating S3 clients with different credentials
        result_collector: Collects and aggregates test results
        session: Current test session (if executing)
    """
    
    def __init__(self, config: S3TestConfiguration, dry_run: bool = False) -> None:
        """Initialize the execution engine.
        
        Args:
            config: S3 test configuration with scenarios and settings
            dry_run: If True, simulate operations without actual API calls
        """
        self.config = config
        self.dry_run = dry_run
        self.logger = get_logger("core.engine")
        
        # Initialize components
        self.client_factory = S3ClientFactory(config.config)
        self.result_collector = ResultCollector()
        
        # 디버그 모드 설정 (환경 변수에서 가져옴)
        self.debug_mode = os.environ.get("S3TESTER_DEBUG", "false").lower() == "true"
        
        # Execution state
        self.session: Optional[S3TestSession] = None
        self._cancelled = False
        
    async def execute_tests(self, 
                          group_names: Optional[List[str]] = None,
                          parallel: Optional[bool] = None) -> S3TestSession:
        """Execute test scenarios and return results.
        
        Args:
            group_names: Optional list of group names to execute. If None, all groups are executed
            parallel: If True, execute operations in parallel. If None, use config default
            
        Returns:
            S3TestSession containing execution results and metadata
            
        Raises:
            ExecutionError: If test execution fails
            ConfigurationError: If configuration is invalid
            
        Example:
            >>> engine = S3TestExecutionEngine(config)
            >>> session = await engine.execute_tests(group_names=['basic-ops'])
            >>> print(f"Tests completed: {session.summary.passed}/{session.summary.total}")
        """
        
        # Initialize test session
        session_id = str(uuid.uuid4())
        self.session = S3TestSession(
            session_id=session_id,
            config_file=self.config.config_file_path or Path("unknown"),
            start_time=datetime.utcnow()
        )
        
        # 작업 카운터 사용하지 않음
        
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
    
    def _filter_groups(self, group_names: Optional[List[str]]) -> List[S3TestGroup]:
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
    
    async def _execute_groups_parallel(self, groups: List[S3TestGroup]):
        """Execute test groups in parallel."""
        self.logger.info(f"Executing {len(groups)} groups in parallel")
        
        # Create tasks for each group
        tasks = []
        for group in groups:
            task = asyncio.create_task(self._execute_group(group))
            tasks.append(task)
        
        # Wait for all groups to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_groups_sequential(self, groups: List[S3TestGroup]):
        """Execute test groups sequentially."""
        self.logger.info(f"Executing {len(groups)} groups sequentially")
        
        for group in groups:
            if self._cancelled:
                break
            await self._execute_group(group)
    
    async def _execute_group(self, group: S3TestGroup):
        """Execute a single test group with before/test/after phases."""
        group_logger = get_logger(f"core.engine.{group.name}")
        group_logger.info(f"Starting test group: {group.name}")
        
        # Update group status
        group.set_status(S3TestGroupStatus.RUNNING_BEFORE)
        
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
                    # before_test 작업이 실패했지만 테스트를 계속 진행합니다
                    group_logger.error("Before-test operations failed, continuing with test and after-test")
            
            # Phase 2: Test operations
            group.set_status(S3TestGroupStatus.RUNNING_TEST)
            group_logger.info(f"Executing {len(group.test)} test operations")
            await self._execute_operations(group.test, group, client, "test")
            
            # Phase 3: After test operations (cleanup)
            if group.after_test:
                group.set_status(S3TestGroupStatus.RUNNING_AFTER)
                group_logger.info(f"Executing {len(group.after_test)} after-test operations")
                await self._execute_operations(group.after_test, group, client, "after")
            
            group.set_status(S3TestGroupStatus.COMPLETED)
            group_logger.info(f"Test group completed in {group.duration:.2f}s")
            
        except Exception as e:
            group.set_status(S3TestGroupStatus.FAILED)
            group_logger.error(f"Test group failed: {e}")
            raise
    
    def _get_client_for_group(self, group: S3TestGroup) -> boto3.client:
        """Get S3 client for test group."""
        credential_name = group.credential
        credential = self.config.config.get_credential(credential_name)
        
        if not credential:
            raise ValueError(f"Credential not found: {credential_name}")
        
        return self.client_factory.create_client(credential)
    
    async def _execute_operations(self, 
                                operations: List[Operation],
                                group: S3TestGroup,
                                default_client: boto3.client,
                                phase: str) -> bool:
        """Execute a list of operations sequentially."""
        if not operations:
            return True
        
        # For before-test operations, fail fast
        # For test operations, continue on failure
        # For after-test operations, continue on failure (cleanup)
        fail_fast = (phase == "before")
        
        success_count = 0
        
        # 순차적으로 작업 실행
        loop = asyncio.get_event_loop()
        total_operations = len(operations)
        
        for index, operation in enumerate(operations, 1):  # 1-based index
            self.logger.info(f"Executing operation {operation.operation} sequentially...")
            
            # 단일 작업 실행 (순차적으로)
            try:
                # 비동기 컨텍스트에서 동기 함수 실행
                result = await loop.run_in_executor(
                    None,  # 기본 executor 사용
                    self._execute_single_operation,
                    operation, group, default_client, phase, index, total_operations
                )
                
                # 결과 처리 - 결과는 TestResult.status 값이 PASS인지 여부
                if result:
                    success_count += 1
                elif fail_fast:
                    # 마지막 결과 가져오기 (방금 추가된 것)
                    if self.session and self.session.results:
                        last_result = self.session.results[-1]
                        error_msg = last_result.error_message if last_result.error_message else "Unknown error"
                        self.logger.error(f"Operation {operation.operation} failed with error: {error_msg}")
                    else:
                        self.logger.error(f"Operation {operation.operation} failed with fail_fast=True, stopping execution")
                    return False
                
            except Exception as e:
                self.logger.error(f"Operation {operation.operation} failed with exception: {e}")
                if fail_fast:
                    return False
        
        # 작업 성공 여부 반환 
        # before_test에서는 최소 하나 이상 성공해야 함
        # 다른 단계에서는 실패해도 계속 진행
        self.logger.info(f"Phase {phase} completed with {success_count}/{len(operations)} successful operations")
        return success_count > 0 if fail_fast else True
    
    def _execute_single_operation(self, 
                                operation: Operation,
                                group: S3TestGroup,
                                default_client: boto3.client,
                                phase: str,
                                phase_index: int,
                                phase_total: int) -> bool:
        """Execute a single operation (runs in thread pool)."""
        
        # 작업 번호를 사용하지 않음
        operation_number = 0  # 로깅에서만 참조되므로 0으로 설정
        
        # Get client (use override if specified)
        client = default_client
        if operation.credential:
            credential = self.config.config.get_credential(operation.credential)
            if credential:
                client = self.client_factory.create_client(credential)
        
        # 설정 파일의 디렉토리 경로 결정
        config_dir = self.config.config_file_path.parent if self.config.config_file_path else Path.cwd()
        self.logger.debug(f"Using config directory: {config_dir} for operation: {operation.operation}")
        
        # _config_dir 매개변수 추가
        params_with_config_dir = operation.parameters.copy()
        params_with_config_dir['_config_dir'] = config_dir
        operation = operation.model_copy(update={'parameters': params_with_config_dir})
        
        # Resolve file paths relative to config directory
        resolved_operation = operation.resolve_file_paths(config_dir)
        
        # Create operation context
        context = OperationContext(
            s3_client=client,
            operation_name=operation.operation,
            parameters=resolved_operation.parameters,
            config_dir=config_dir,
            dry_run=self.dry_run
        )
        
        # Get operation implementation
        op_impl = OperationRegistry.get_operation(operation.operation)
        
        # Execute operation
        op_result = op_impl.execute(context)
        
        # Create test result with phase information
        test_result = S3TestResult(
            operation_name=operation.operation,
            group_name=group.name,
            expected=operation.expected_result,
            phase_name=phase,
            phase_index=phase_index,
            phase_total=phase_total
        )
        
        # Update result based on execution
        test_result.set_result(
            success=op_result.success,
            duration=op_result.duration,
            actual_response=op_result.response,
            error_message=op_result.error_message
        )
        
        # Set ERROR status for system-level failures (not S3 API errors)
        if op_result.raw_exception and not hasattr(op_result.raw_exception, 'response'):
            # This is a system error (network, timeout, etc.), not an S3 API error
            test_result.status = S3TestResultStatus.ERROR
        
        # 작업 번호를 더 이상 사용하지 않음
        
        # Add to session results
        if self.session:
            self.session.add_result(test_result)
        
        # Log result
        status_emoji = "✅" if test_result.status == S3TestResultStatus.PASS else "❌"
        
        if test_result.status == S3TestResultStatus.PASS:
            self.logger.info(
                f"{status_emoji} {group.name} > {operation.operation} "
                f"({test_result.status.value}) [{test_result.duration:.2f}s]"
            )
        else:
            # 실패한 경우 오류 메시지와 함께 표시
            error_msg = test_result.error_message if test_result.error_message else "Unknown error"
            self.logger.info(
                f"{status_emoji} {group.name} > {operation.operation} "
                f"({test_result.status.value}) [{test_result.duration:.2f}s] - {error_msg}"
            )
            
            # 상세 정보도 로깅 (debug 레벨)
            if test_result.error_message:
                self.logger.debug(f"Detailed error for {operation.operation}: {test_result.error_message}")
                
            # 디버그 모드일 때 상세 정보 저장
            if self.debug_mode:
                try:
                    # 디버그 디렉토리 생성
                    debug_dir = Path(self.config.config_file_path).parent / "debug_logs"
                    debug_dir.mkdir(exist_ok=True)
                    
                    # 실패 정보 저장 (번호 없이)
                    fail_file = debug_dir / f"fail_{operation.operation}.json"
                    
                    # 실패 정보 기록
                    with open(fail_file, "w") as f:
                        # TestResult를 사전으로 변환하여 저장
                        result_dict = {
                            "operation_name": test_result.operation_name,
                            "group_name": test_result.group_name,
                            "status": test_result.status,
                            "duration": test_result.duration,
                            "error_message": test_result.error_message,
                            "actual_response": op_result.response,  # 직접 OperationResult에서 가져옴
                        }
                        
                        # 안전하게 JSON 직렬화
                        json.dump(result_dict, f, default=lambda x: str(x), indent=2)
                        
                    self.logger.debug(f"Failed operation details saved to {fail_file}")
                except Exception as e:
                    self.logger.error(f"Failed to save debug info: {e}")
        
        return test_result.status == S3TestResultStatus.PASS
    
    def cancel(self):
        """Cancel test execution."""
        self._cancelled = True
        self.logger.info("Test execution cancellation requested")

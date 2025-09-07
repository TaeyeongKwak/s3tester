"""
Core facade for s3tester.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional

from s3tester.cli.config_loader import ConfigLoader, ConfigurationLoadError
from s3tester.operations.registry import OperationRegistry
from .engine import TestExecutionEngine


class S3TesterFacade:
    """Facade class providing high-level access to s3tester functionality."""
    
    def __init__(self):
        """Initialize the facade."""
        self.config_loader = ConfigLoader()
    
    def validate_configuration(self, config_path: str, strict: bool = False) -> tuple:
        """Validate configuration without running tests.
        
        Returns:
            tuple: (is_valid: bool, issues: list) - Validation result and list of issues if any
        """
        try:
            # Use the actual config loader for proper validation
            test_config = self.config_loader.load_and_validate(Path(config_path))
            
            # If we get here, basic validation passed
            issues = []
            
            # Additional strict validation if requested
            if strict:
                # Check for potential issues that aren't errors but could be problems
                if not test_config.config.credentials:
                    issues.append("No credentials configured")
                
                if not test_config.test_cases.groups:
                    issues.append("No test groups defined")
                
                # Check if operations are supported
                unsupported_ops = []
                for group in test_config.test_cases.groups:
                    for test_case in (group.before_test or []) + group.test + (group.after_test or []):
                        if test_case.operation not in OperationRegistry.list_operations():
                            unsupported_ops.append(test_case.operation)
                
                if unsupported_ops:
                    issues.append(f"Unsupported operations: {', '.join(set(unsupported_ops))}")
            
            return True, issues
            
        except ConfigurationLoadError as e:
            return False, [str(e)]
        except Exception as e:
            error_msg = f"Validation error: {e}"
            return False, [error_msg]
    
    def get_available_operations(self) -> List[str]:
        """Return list of available operations."""
        return sorted(OperationRegistry.list_operations())
    
    def run_tests(self, config_path: str, 
                group_names: Optional[List[str]] = None,
                parallel: Optional[bool] = None,
                dry_run: bool = False) -> Dict[str, Any]:
        """Run tests according to configuration."""
        try:
            # Load and validate configuration first
            test_config = self.config_loader.load_and_validate(Path(config_path))
            
            # Create and run the test execution engine
            engine = TestExecutionEngine(test_config, dry_run=dry_run)
            
            # Execute tests using asyncio
            session = asyncio.run(engine.execute_tests(
                group_names=group_names,
                parallel=parallel
            ))
            
            # Convert TestSession to facade response format
            # 예상된 에러를 계산에 반영
            expected_errors_count = sum(
                1 for result in session.results 
                if (result.status == "fail" or result.status == "error") and
                   not result.expected.success and 
                   result.expected.error_code and 
                   result.actual and 
                   result.actual.get('Error', {}).get('Code') == result.expected.error_code
            )
            
            total_operations = session.summary.passed + session.summary.failed + session.summary.error
            # 예상된 에러도 성공으로 간주
            successful_operations = session.summary.passed + expected_errors_count
            # 예상치 않은 에러만 실패로 간주
            failed_operations = (session.summary.failed + session.summary.error) - expected_errors_count
            
            # Collect detailed failure information
            failures = []
            for result in session.results:
                if result.status != "pass":
                    # 예상된 에러인지 여부 확인
                    is_expected_error = (
                        not result.expected.success and 
                        result.expected.error_code and 
                        result.actual and 
                        result.actual.get('Error', {}).get('Code') == result.expected.error_code
                    )
                    
                    # 예상된 에러가 아닌 경우만 failures 목록에 추가
                    if not is_expected_error:
                        # 추가 정보 포함
                        failure_info = {
                            "group": result.group_name,
                            "operation": result.operation_name,
                            "error": result.error_message if result.error_message else "Unknown error",
                            "status": result.status,
                            "duration": result.duration,
                            "expected_error": is_expected_error,
                            "phase_name": result.phase_name,
                            "phase_index": result.phase_index,
                            "phase_total": result.phase_total
                        }
                        
                        failures.append(failure_info)
            
            # Calculate average duration of operations
            avg_duration_ms = 0
            if session.results:
                operation_durations = [result.duration * 1000 for result in session.results]  # Convert seconds to ms
                if operation_durations:
                    avg_duration_ms = sum(operation_durations) / len(operation_durations)
                
            return {
                "session_id": session.session_id,
                "total": total_operations,
                "successful": successful_operations,
                "failed": failed_operations,
                "success_rate": (successful_operations / total_operations * 100) if total_operations > 0 else 0,
                "duration": session.duration,
                "avg_duration_ms": avg_duration_ms,
                "groups_executed": len(set(result.group_name for result in session.results)),
                "parallel": parallel if parallel is not None else test_config.test_cases.parallel,
                "dry_run": dry_run,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "failures": failures if failures else []
            }
            
        except ConfigurationLoadError as e:
            import traceback
            error_detail = traceback.format_exc()
            return {
                "total": 0,
                "successful": 0,
                "failed": 1,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0,
                "error": str(e),
                "error_detail": error_detail
            }
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {
                "total": 0,
                "successful": 0,
                "failed": 1,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0,
                "error": f"Execution error: {e}",
                "error_detail": error_detail
            }

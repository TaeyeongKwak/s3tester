"""
Command-line interface for s3tester.
"""
from __future__ import annotations

import os
import sys
import time
import json
import asyncio
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.text import Text

from .__version__ import __version__
from .cli.config_loader import ConfigLoader, ConfigurationLoadError
from .config.models import S3TestConfiguration
from .core.engine import S3TestExecutionEngine
from .core.result_collector import ResultCollector
from .core.logging_config import setup_logging, get_logger
from .operations.registry import OperationRegistry
from .reporting.formatters import OutputFormat, get_formatter


console = Console()

# Environment variable prefixes
ENV_PREFIX = "S3TESTER_"


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-v", "--version")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Set logging level"
)
@click.option(
    "--log-format",
    type=click.Choice(["standard", "json"]),
    default="standard",
    help="Set logging format"
)
@click.option(
    "--log-file",
    type=click.Path(),
    help="Log file path"
)
@click.pass_context
def cli(ctx, log_level: str, log_format: str, log_file: Optional[str]) -> None:
    """
    S3 API compatibility testing tool.
    
    Test AWS S3 compatible APIs with customizable test scenarios.
    """
    # Setup logging early
    setup_logging(
        log_level=log_level,
        json_format=(log_format == "json"),
        log_file=log_file
    )
    
    # Store logging config in context
    ctx.ensure_object(dict)
    ctx.obj["logger"] = get_logger("cli")


@cli.command("run")
@click.option(
    "-c", "--config",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to the test configuration file (YAML).",
)
@click.option(
    "-p", "--parallel/--no-parallel",
    default=None,
    help="Override parallel execution setting from config.",
)
@click.option(
    "-g", "--group",
    multiple=True,
    help="Run only specific test groups (can specify multiple times).",
)
@click.option(
    "-o", "--output",
    type=click.Path(dir_okay=False, writable=True),
    help="Write output to a file instead of stdout.",
)
@click.option(
    "-f", "--format",
    type=click.Choice(["json", "yaml", "table", "console"], case_sensitive=False),
    default="console",
    help="Output format for test results.",
)
@click.option(
    "-t", "--timeout",
    type=int,
    default=None,
    help="Timeout in seconds for each operation.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate configuration without executing tests.",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Show detailed output including response information for failed operations.",
)
@click.pass_context
def run_command(
    ctx,
    config: str,
    parallel: Optional[bool],
    group: List[str],
    output: Optional[str],
    format: str,
    timeout: Optional[int],
    dry_run: bool,
    verbose: bool,
) -> None:
    """
    Run S3 compatibility tests.
    
    This command executes tests defined in the configuration file against
    the specified S3 endpoint. Tests can be run in parallel or sequentially.
    """
    # Configure output
    output_file = open(output, "w") if output else sys.stdout
    
    # Logging is already configured in the main CLI group
    logger = ctx.obj.get("logger") if ctx.obj else get_logger("cli")
    
    try:
        # Load and validate configuration
        config_loader = ConfigLoader()
        try:
            test_config = config_loader.load_and_validate(config, dry_run=dry_run)
        except ConfigurationLoadError as e:
            error_text = Text()
            error_text.append("Error: ", style="bold red")
            error_text.append(str(e))
            console.print(error_text)
            sys.exit(2)
        
        if dry_run:
            valid_text = Text("Configuration is valid.", style="bold green")
            console.print(valid_text)
            sys.exit(0)
        
        # Create and configure test engine
        engine = S3TestExecutionEngine(test_config, dry_run=False)
        
        # Apply command-line overrides
        if group:
            group_list = list(group)
        else:
            group_list = None
        
        # Run tests
        start_time = time.time()
        start_text = Text(f"Starting tests with {len(test_config.test_cases.groups)} groups...", style="bold")
        console.print(start_text)
        
        try:
            session = asyncio.run(engine.execute_tests(
                group_names=group_list, 
                parallel=parallel
            ))
            
            # Format and output results using the specified format
            try:
                formatter = get_formatter(format)
                
                # Special handling for console format with verbose mode
                if format.lower() == "console" and verbose:
                    # Use custom console output with verbose details
                    console.print("\nTest Results:")
                    console.print(f"Success Rate: {session.summary.success_rate * 100:.1f}%")
                    console.print(f"Total Operations: {session.summary.passed + session.summary.failed + session.summary.error}")
                    console.print(f"Successful Operations: {session.summary.passed}")
                    console.print(f"Failed Operations: {session.summary.failed + session.summary.error}")
                    
                    # Calculate average duration for operations
                    if session.results:
                        durations = [r.duration for r in session.results]
                        avg_duration = sum(durations) / len(durations) if durations else 0
                        console.print(f"Average Duration: {avg_duration * 1000:.2f}ms")
                    else:
                        console.print("Average Duration: 0.00ms")
                    
                    # Show failed operations if any
                    failed_ops = [r for r in session.results if r.status != "pass"]
                    if failed_ops:
                        console.print("\nFailed Operations:")
                        for op in failed_ops:
                            console.print(f"  - {op.group_name}: {op.operation_name} - {op.error_message}")
                            
                            # 상세 정보는 verbose 모드에서만 표시
                            if verbose:
                                # 디버그 로그 폴더 확인
                                debug_dir = Path(test_config.config_file_path).parent / "debug_logs"
                                
                                # 디버그 로그 파일 검색 (작업명으로 시작하는 가장 최근 파일)
                                actual_response = None
                                debug_files = list(debug_dir.glob(f"fail_{op.operation_name}*.json"))
                                debug_file = max(debug_files, key=lambda f: f.stat().st_mtime) if debug_files else None
                                
                                # 로그 파일이 있으면 읽기
                                if debug_file and debug_file.exists():
                                    try:
                                        with open(debug_file, 'r') as f:
                                            debug_data = json.load(f)
                                            if 'actual_response' in debug_data:
                                                actual_response = debug_data['actual_response']
                                    except Exception as e:
                                        if verbose:
                                            console.print(f"    [디버그 파일 읽기 오류: {str(e)}]")
                                
                                # 응답 정보 표시
                                console.print("\n    Response Details:")
                                
                                # 먼저 op.actual 확인
                                if op.actual and isinstance(op.actual, dict):
                                    resp_data = op.actual
                                # 디버그 파일에서 읽은 정보 확인 
                                elif actual_response and isinstance(actual_response, dict):
                                    resp_data = actual_response
                                else:
                                    resp_data = None
                                
                                if resp_data:
                                    if 'Error' in resp_data:
                                        # 에러 응답 상세 정보
                                        error_info = resp_data['Error']
                                        console.print(f"    - Error Code: {error_info.get('Code', 'Unknown')}")
                                        console.print(f"    - Error Message: {error_info.get('Message', 'No message')}")
                                        if 'ResponseMetadata' in resp_data and 'RequestId' in resp_data['ResponseMetadata']:
                                            console.print(f"    - Request ID: {resp_data['ResponseMetadata'].get('RequestId')}")
                                        # 에러 응답의 추가 정보 표시
                                        if isinstance(error_info, dict):
                                            extra_error_info = {k:v for k,v in error_info.items() 
                                                              if k not in ['Code', 'Message']}
                                            if extra_error_info:
                                                for key, value in extra_error_info.items():
                                                    console.print(f"    - {key}: {value}")
                                    else:
                                        # 일반 응답 정보
                                        console.print(f"    - Status Code: {resp_data.get('ResponseMetadata', {}).get('HTTPStatusCode', 'Unknown')}")
                                        # 주요 응답 데이터 표시 (최대 5개 항목)
                                        response_data = {k:v for k,v in resp_data.items() if k not in ['ResponseMetadata', 'Error']}
                                        if response_data:
                                            console.print("    - Response Data:")
                                            for i, (key, value) in enumerate(response_data.items()):
                                                if i < 5:  # 응답 데이터 최대 5개만 표시
                                                    console.print(f"      {key}: {str(value)[:200]}")  # 값 길이 제한
                                else:
                                    console.print("    [No response data available]")
                                    
                                # 기대값과 실제값 비교 정보 표시
                                if hasattr(op, 'expected') and op.expected:
                                    console.print("    Expected vs Actual:")
                                    if isinstance(op.expected, dict):
                                        if 'success' in op.expected:
                                            console.print(f"    - Expected Success: {op.expected['success']}, Actual: {'success' if op.status == 'pass' else 'failure'}")
                                        if 'error_code' in op.expected and op.expected['error_code']:
                                            actual_error_code = resp_data.get('Error', {}).get('Code', 'None') if resp_data else 'None'
                                            console.print(f"    - Expected Error Code: {op.expected['error_code']}, Actual: {actual_error_code}")
                                    elif hasattr(op.expected, 'success'):
                                        console.print(f"    - Expected Success: {op.expected.success}, Actual: {'success' if op.status == 'pass' else 'failure'}")
                                        if hasattr(op.expected, 'error_code') and op.expected.error_code:
                                            actual_error_code = resp_data.get('Error', {}).get('Code', 'None') if resp_data else 'None'
                                            console.print(f"    - Expected Error Code: {op.expected.error_code}, Actual: {actual_error_code}")
                else:
                    # Use the formatter for all other formats or console without verbose
                    formatter.format_session(session, output_file)
            except Exception as e:
                console.print(f"Error formatting results: {e}")
                if hasattr(session, 'error'):
                    console.print(f"Error running tests: {session.error}")
            
            # Determine exit code based on test results
            exit_code = 0 if session.summary.passed > 0 and session.summary.failed == 0 and session.summary.error == 0 else 1
            
            # Print summary to console if output is redirected
            if output:
                complete_text = Text(f"Test session complete: {session.session_id}", style="bold")
                console.print(complete_text)
                console.print(f"Results: {session.summary.passed} passed, {session.summary.failed} failed, {session.summary.error} errors")
                console.print(f"Duration: {session.duration:.2f} seconds")
                console.print(f"Results written to: {output}")
            
            sys.exit(exit_code)
            
        except Exception as e:
            error_text = Text()
            error_text.append("Error during test execution: ", style="bold red")
            error_text.append(str(e))
            console.print(error_text)
            import traceback
            trace_text = Text()
            trace_text.append("Traceback: ", style="bold red")
            trace_text.append(traceback.format_exc())
            console.print(trace_text)
            sys.exit(3)
            
    finally:
        # Close output file if opened
        if output and output_file != sys.stdout:
            output_file.close()


@cli.command("validate")
@click.option(
    "-c", "--config",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to the test configuration file (YAML).",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Perform strict validation (treat warnings as errors).",
)
def validate_command(config: str, strict: bool) -> None:
    """
    Validate a test configuration file without executing tests.
    
    This command checks that the configuration file is correctly formatted
    and contains valid test definitions.
    """
    config_loader = ConfigLoader()
    try:
        test_config = config_loader.load_and_validate(config, strict=strict, dry_run=True)
        console.print(f"[bold green]Configuration is valid.[/] Found:")
        console.print(f"- {len(test_config.config.credentials)} credential sets")
        console.print(f"- {len(test_config.test_cases.groups)} test groups")
        
        total_operations = sum(
            len(group.before_test or []) + 
            len(group.test or []) + 
            len(group.after_test or []) 
            for group in test_config.test_cases.groups
        )
        console.print(f"- {total_operations} total operations")
        
        sys.exit(0)
    except ConfigurationLoadError as e:
        console.print(f"[bold red]Validation failed:[/] {str(e)}")
        sys.exit(2)


@cli.command("list")
@click.option(
    "-c", "--config",
    required=False,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to the test configuration file (YAML). Required unless --supported-operations is used.",
)
@click.option(
    "--credentials",
    is_flag=True,
    help="List credential sets defined in the configuration.",
)
@click.option(
    "--groups",
    is_flag=True,
    help="List test groups defined in the configuration.",
)
@click.option(
    "--operations",
    is_flag=True,
    help="List operations defined in the configuration.",
)
@click.option(
    "--supported-operations",
    is_flag=True,
    help="List all supported S3 operations.",
)
def list_command(
    config: str,
    credentials: bool,
    groups: bool,
    operations: bool,
    supported_operations: bool,
) -> None:
    """
    List configuration components and supported operations.
    
    This command lists various elements from the configuration file,
    such as credential sets, test groups, and operations.
    """
    if supported_operations:
        registry = OperationRegistry()
        
        console.print("[bold]Supported S3 Operations:[/]")
        for op_name in sorted(registry.list_operations()):
            console.print(f"  - {op_name}")
        
        sys.exit(0)
    
    # 설정 파일이 제공되지 않았을 때 오류 표시
    if not config:
        console.print("[bold red]Error:[/] --config option is required unless --supported-operations is used.")
        sys.exit(2)
    
    # Load configuration file
    config_loader = ConfigLoader()
    try:
        test_config = config_loader.load_and_validate(config, strict=False, dry_run=True)
    except ConfigurationLoadError as e:
        console.print(f"[bold red]Error loading configuration:[/] {str(e)}")
        sys.exit(2)
    
    # Default behavior: list everything if no specific option is chosen
    show_all = not (credentials or groups or operations)
    
    # List credentials
    if credentials or show_all:
        console.print("[bold]Credential Sets:[/]")
        for cred in test_config.config.credentials:
            console.print(f"  - {cred.name}")
        console.print()
    
    # List groups
    if groups or show_all:
        console.print("[bold]Test Groups:[/]")
        for group in test_config.test_cases.groups:
            total_ops = len(group.before_test or []) + len(group.test or []) + len(group.after_test or [])
            console.print(f"  - {group.name} ({total_ops} operations)")
        console.print()
    
    # List operations
    if operations or show_all:
        console.print("[bold]Operations by Group:[/]")
        for group in test_config.test_cases.groups:
            console.print(f"\n[bold cyan]{group.name}:[/]")
            
            if group.before_test:
                console.print("  [bold]Before-test operations:[/]")
                for op in group.before_test:
                    credential = op.credential or group.credential
                    console.print(f"    - {op.operation} (credential: {credential})")
            
            if group.test:
                console.print("  [bold]Test operations:[/]")
                for op in group.test:
                    credential = op.credential or group.credential
                    console.print(f"    - {op.operation} (credential: {credential})")
            
            if group.after_test:
                console.print("  [bold]After-test operations:[/]")
                for op in group.after_test:
                    credential = op.credential or group.credential
                    console.print(f"    - {op.operation} (credential: {credential})")
    
    sys.exit(0)


def main() -> None:
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        console.print(f"[bold red]Unhandled error:[/] {str(e)}")
        if os.getenv(f"{ENV_PREFIX}DEBUG"):
            import traceback
            console.print("[bold red]Traceback:[/]")
            console.print(traceback.format_exc())
        sys.exit(3)


if __name__ == "__main__":
    main()

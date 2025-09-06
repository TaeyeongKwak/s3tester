"""
Command-line interface for s3tester.
"""
from __future__ import annotations

import os
import sys
import time
import asyncio
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console

from .__version__ import __version__
from .cli.config_loader import ConfigLoader, ConfigurationLoadError
from .config.models import TestConfiguration
from .core.engine import TestExecutionEngine
from .core.result_collector import ResultCollector
from .operations.registry import OperationRegistry
from .reporting.formatters import OutputFormat, get_formatter


console = Console()

# Environment variable prefixes
ENV_PREFIX = "S3TESTER_"


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-v", "--version")
def cli() -> None:
    """
    S3 API compatibility testing tool.
    
    Test AWS S3 compatible APIs with customizable test scenarios.
    """
    pass


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
def run_command(
    config: str,
    parallel: Optional[bool],
    group: List[str],
    output: Optional[str],
    format: str,
    timeout: Optional[int],
    dry_run: bool,
) -> None:
    """
    Run S3 compatibility tests.
    
    This command executes tests defined in the configuration file against
    the specified S3 endpoint. Tests can be run in parallel or sequentially.
    """
    # Configure output
    output_file = open(output, "w") if output else sys.stdout
    try:
        # Load and validate configuration
        config_loader = ConfigLoader()
        try:
            test_config = config_loader.load_and_validate(config, dry_run=dry_run)
        except ConfigurationLoadError as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
            sys.exit(2)
        
        if dry_run:
            console.print("[bold green]Configuration is valid.[/]")
            sys.exit(0)
        
        # Create and configure test engine
        engine = TestExecutionEngine(test_config, dry_run=False)
        
        # Apply command-line overrides
        if group:
            group_list = list(group)
        else:
            group_list = None
        
        # Run tests
        start_time = time.time()
        console.print(f"[bold]Starting tests with {len(test_config.test_cases.groups)} groups...[/]")
        
        try:
            session = asyncio.run(engine.execute_tests(
                group_names=group_list, 
                parallel=parallel
            ))
            
            # Format and output results
            formatter = get_formatter(format.upper())
            formatter.format_session(session, output_file)
            
            # Determine exit code based on test results
            exit_code = 0 if session.summary.passed > 0 and session.summary.failed == 0 and session.summary.error == 0 else 1
            
            # Print summary to console if output is redirected
            if output:
                console.print(f"[bold]Test session complete: {session.session_id}[/]")
                console.print(f"Results: {session.summary.passed} passed, {session.summary.failed} failed, {session.summary.error} errors")
                console.print(f"Duration: {session.duration:.2f} seconds")
                console.print(f"Results written to: {output}")
            
            sys.exit(exit_code)
            
        except Exception as e:
            console.print(f"[bold red]Error during test execution:[/] {str(e)}")
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
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to the test configuration file (YAML).",
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

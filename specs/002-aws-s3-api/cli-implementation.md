# CLI Implementation Guide

## Command-Line Interface Architecture

### Main CLI Module

**File**: `src/s3tester/cli.py`

```python
import asyncio
import sys
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.table import Table
from rich import print as rich_print

from .config.models import TestConfiguration
from .core.engine import TestExecutionEngine
from .core.validator import ConfigurationValidator
from .core.progress import TestProgressTracker
from .reporting.formatters import OutputFormatter
from .operations.registry import OperationRegistry
import logging

# Configure logging
def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )

# Global console instance
console = Console()

@click.group(invoke_without_command=True)
@click.option('--config', '-c', 
              type=click.Path(exists=True, path_type=Path),
              help='Path to YAML configuration file',
              required=False)
@click.option('--dry-run', 
              is_flag=True,
              help='Validate configuration without executing operations')
@click.option('--format',
              type=click.Choice(['table', 'json', 'yaml']),
              default='table',
              help='Output format')
@click.option('--verbose', '-v',
              is_flag=True,
              help='Enable verbose logging')
@click.option('--version',
              is_flag=True,
              help='Show version information')
@click.pass_context
def cli(ctx: click.Context, 
        config: Optional[Path], 
        dry_run: bool,
        format: str,
        verbose: bool,
        version: bool):
    """S3 API compatibility testing tool."""
    
    # Show version and exit
    if version:
        from . import __version__
        click.echo(f"s3tester {__version__}")
        return
    
    # Setup logging
    setup_logging(verbose)
    
    # Store context
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['dry_run'] = dry_run
    ctx.obj['format'] = format
    ctx.obj['verbose'] = verbose
    
    # If no command specified, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

@cli.command()
@click.option('--parallel/--sequential',
              default=None,
              help='Execute tests in parallel or sequential mode')
@click.option('--group',
              multiple=True,
              help='Run specific test group (can be used multiple times)')
@click.option('--output',
              type=click.Path(path_type=Path),
              help='Save results to file')
@click.option('--timeout',
              type=int,
              default=300,
              help='Operation timeout in seconds')
@click.option('--no-progress',
              is_flag=True,
              help='Disable progress display')
@click.pass_context
def run(ctx: click.Context,
        parallel: Optional[bool],
        group: List[str],
        output: Optional[Path],
        timeout: int,
        no_progress: bool):
    """Execute test scenarios defined in configuration file."""
    
    # Validate required parameters
    config_path = ctx.obj.get('config_path')
    if not config_path:
        # Try environment variable
        import os
        config_env = os.getenv('S3TESTER_CONFIG')
        if config_env:
            config_path = Path(config_env)
        else:
            click.echo("Error: Configuration file required. Use --config or set S3TESTER_CONFIG.", err=True)
            ctx.exit(2)
    
    dry_run = ctx.obj['dry_run']
    format_type = ctx.obj['format']
    
    try:
        # Load configuration
        config = TestConfiguration.load_from_file(config_path)
        
        # Validate configuration
        validator = ConfigurationValidator()
        is_valid, errors = validator.validate_configuration(config, strict=not dry_run)
        
        if not is_valid:
            console.print("[red]Configuration validation failed:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            ctx.exit(2)
        
        # Create engine
        engine = TestExecutionEngine(config, dry_run=dry_run)
        
        # Execute tests with progress tracking
        show_progress = not no_progress and format_type == 'table'
        
        with TestProgressTracker(console, show_progress) as progress:
            # Calculate totals for progress
            groups = config.test_cases.groups
            if group:
                groups = [g for g in groups if g.name in group]
            
            total_groups = len(groups)
            total_operations = sum(len(g.get_all_operations()) for g in groups)
            
            if show_progress:
                progress.start_session(total_groups, total_operations)
            
            # Run tests
            session = asyncio.run(engine.execute_tests(
                group_names=list(group) if group else None,
                parallel=parallel
            ))
        
        # Format and display results
        formatter = OutputFormatter(format_type)
        
        if format_type == 'table':
            _display_table_results(session, console)
        else:
            formatted_output = formatter.format_session(session)
            
            if output:
                output.write_text(formatted_output)
                console.print(f"Results saved to: {output}")
            else:
                click.echo(formatted_output)
        
        # Exit with appropriate code
        if session.summary.failed > 0 or session.summary.error > 0:
            ctx.exit(1)  # Tests failed
        else:
            ctx.exit(0)  # All tests passed
            
    except FileNotFoundError as e:
        console.print(f"[red]File not found: {e}[/red]")
        ctx.exit(2)
    except Exception as e:
        console.print(f"[red]Runtime error: {e}[/red]")
        if ctx.obj['verbose']:
            import traceback
            console.print(traceback.format_exc())
        ctx.exit(3)

@cli.command()
@click.option('--strict',
              is_flag=True,
              help='Enable strict validation (check file existence, credentials)')
@click.pass_context
def validate(ctx: click.Context, strict: bool):
    """Validate configuration file structure and syntax."""
    
    config_path = ctx.obj.get('config_path')
    if not config_path:
        click.echo("Error: Configuration file required. Use --config.", err=True)
        ctx.exit(2)
    
    try:
        # Load configuration
        console.print(f"Validating configuration: {config_path}")
        config = TestConfiguration.load_from_file(config_path)
        
        # Validate configuration
        validator = ConfigurationValidator()
        is_valid, errors = validator.validate_configuration(config, strict=strict)
        
        if is_valid:
            console.print("[green]✅ Configuration is valid[/green]")
            
            # Show summary
            total_groups = len(config.test_cases.groups)
            total_operations = sum(len(g.get_all_operations()) for g in config.test_cases.groups)
            total_credentials = len(config.config.credentials)
            
            console.print(f"  • Groups: {total_groups}")
            console.print(f"  • Operations: {total_operations}")
            console.print(f"  • Credentials: {total_credentials}")
            
            ctx.exit(0)
        else:
            console.print("[red]❌ Configuration validation failed:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            ctx.exit(2)
            
    except Exception as e:
        console.print(f"[red]Validation error: {e}[/red]")
        ctx.exit(2)

@cli.command()
@click.argument('resource', 
                type=click.Choice(['groups', 'operations', 'credentials']),
                required=False)
@click.pass_context
def list(ctx: click.Context, resource: Optional[str]):
    """List available operations and test groups."""
    
    if resource == 'operations' or not resource:
        # List supported operations
        operations = OperationRegistry.list_operations()
        
        console.print("[bold]Supported S3 Operations:[/bold]")
        
        # Group operations by category
        operation_categories = {
            'Bucket': [op for op in operations if 'Bucket' in op and 'Object' not in op],
            'Object': [op for op in operations if 'Object' in op and 'Multipart' not in op],
            'Multipart': [op for op in operations if 'Multipart' in op or 'Part' in op],
            'Tagging': [op for op in operations if 'Tagging' in op],
            'Other': [op for op in operations if not any(cat in op for cat in ['Bucket', 'Object', 'Multipart', 'Tagging'])]
        }
        
        for category, ops in operation_categories.items():
            if ops:
                console.print(f"\n[bold cyan]{category} Operations:[/bold cyan]")
                for op in sorted(ops):
                    console.print(f"  • {op}")
    
    if resource in ['groups', 'credentials'] or not resource:
        # Need configuration for groups and credentials
        config_path = ctx.obj.get('config_path')
        if not config_path:
            if resource in ['groups', 'credentials']:
                click.echo("Error: Configuration file required to list groups/credentials. Use --config.", err=True)
                ctx.exit(2)
            return
        
        try:
            config = TestConfiguration.load_from_file(config_path)
            
            if resource == 'groups' or not resource:
                console.print(f"\n[bold]Test Groups in {config_path.name}:[/bold]")
                for group in config.test_cases.groups:
                    total_ops = len(group.get_all_operations())
                    console.print(f"  • {group.name} ({total_ops} operations)")
            
            if resource == 'credentials' or not resource:
                console.print(f"\n[bold]Credentials in {config_path.name}:[/bold]")
                for cred in config.config.credentials:
                    console.print(f"  • {cred.name} (access key: {cred.access_key[:8]}...)")
                    
        except Exception as e:
            console.print(f"[red]Error loading configuration: {e}[/red]")
            ctx.exit(2)

def _display_table_results(session, console: Console):
    """Display results in table format."""
    from .reporting.formatters import TableFormatter
    
    formatter = TableFormatter(console)
    formatter.display_session(session)

# Environment variable support
def load_env_defaults():
    """Load default values from environment variables."""
    import os
    
    env_vars = {
        'S3TESTER_CONFIG': None,
        'S3TESTER_FORMAT': 'table',
        'S3TESTER_TIMEOUT': '300',
        'AWS_PROFILE': None,
        'AWS_DEFAULT_REGION': None
    }
    
    loaded_vars = {}
    for var, default in env_vars.items():
        value = os.getenv(var, default)
        if value:
            loaded_vars[var] = value
    
    return loaded_vars

# Entry point
def main():
    """Main entry point for s3tester CLI."""
    try:
        # Load environment defaults
        env_vars = load_env_defaults()
        
        # Override click defaults with environment variables
        if 'S3TESTER_CONFIG' in env_vars:
            # This would be handled in the command functions
            pass
        
        # Run CLI
        cli()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Test execution interrupted by user[/yellow]")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(3)

if __name__ == '__main__':
    main()
```

### Output Formatters

**File**: `src/s3tester/reporting/formatters.py`

```python
import json
import yaml
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from ..config.models import TestSession, TestResult, TestResultStatus

class OutputFormatter:
    """Base output formatter."""
    
    def __init__(self, format_type: str):
        self.format_type = format_type
    
    def format_session(self, session: TestSession) -> str:
        """Format session results."""
        if self.format_type == 'json':
            return self._format_json(session)
        elif self.format_type == 'yaml':
            return self._format_yaml(session)
        elif self.format_type == 'table':
            # Table format is handled separately with Rich
            return ""
        else:
            raise ValueError(f"Unsupported format: {self.format_type}")
    
    def _format_json(self, session: TestSession) -> str:
        """Format as JSON."""
        session_dict = session.model_dump(mode='json')
        return json.dumps(session_dict, indent=2, default=str)
    
    def _format_yaml(self, session: TestSession) -> str:
        """Format as YAML."""
        session_dict = session.model_dump(mode='json')
        return yaml.dump(session_dict, default_flow_style=False, allow_unicode=True)

class TableFormatter:
    """Rich table formatter for console output."""
    
    def __init__(self, console: Console):
        self.console = console
    
    def display_session(self, session: TestSession):
        """Display session results as formatted tables."""
        
        # Session header
        self._display_session_header(session)
        
        # Results summary table
        self._display_summary_table(session)
        
        # Group details table
        self._display_group_details(session)
        
        # Failed operations (if any)
        failed_results = [r for r in session.results if r.status != TestResultStatus.PASS]
        if failed_results:
            self._display_failures(failed_results)
        
        # Session footer
        self._display_session_footer(session)
    
    def _display_session_header(self, session: TestSession):
        """Display session header information."""
        header_text = Text()
        header_text.append("S3 Test Session\n", style="bold blue")
        header_text.append(f"Session ID: {session.session_id}\n")
        header_text.append(f"Config: {session.config_file.name}\n")
        header_text.append(f"Started: {session.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        panel = Panel(header_text, box=box.ROUNDED, padding=(1, 2))
        self.console.print(panel)
        self.console.print()
    
    def _display_summary_table(self, session: TestSession):
        """Display results summary table."""
        table = Table(title="Test Results Summary", box=box.ROUNDED)
        
        table.add_column("Group", justify="left", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Operations", justify="right")
        table.add_column("Duration", justify="right", style="dim")
        
        # Group results by group name
        from collections import defaultdict
        group_stats = defaultdict(lambda: {'total': 0, 'passed': 0, 'failed': 0, 'error': 0, 'duration': 0.0})
        
        for result in session.results:
            stats = group_stats[result.group_name]
            stats['total'] += 1
            stats['duration'] += result.duration
            
            if result.status == TestResultStatus.PASS:
                stats['passed'] += 1
            elif result.status == TestResultStatus.FAIL:
                stats['failed'] += 1
            elif result.status == TestResultStatus.ERROR:
                stats['error'] += 1
        
        # Add rows to table
        for group_name, stats in group_stats.items():
            if stats['failed'] == 0 and stats['error'] == 0:
                status = f"✅ PASS ({stats['passed']}/{stats['total']})"
                status_style = "green"
            else:
                status = f"❌ FAIL ({stats['passed']}/{stats['total']})"
                status_style = "red"
            
            operations_text = f"{stats['total']} ops"
            duration_text = f"{stats['duration']:.2f}s"
            
            table.add_row(
                group_name,
                Text(status, style=status_style),
                operations_text,
                duration_text
            )
        
        self.console.print(table)
        self.console.print()
    
    def _display_group_details(self, session: TestSession):
        """Display detailed group breakdown."""
        if session.summary.failed == 0 and session.summary.error == 0:
            return  # Skip details if all passed
        
        # Show only failed operations details
        failed_results = [r for r in session.results if r.status != TestResultStatus.PASS]
        
        if failed_results:
            table = Table(title="Failed Operations Details", box=box.ROUNDED)
            table.add_column("Group", style="cyan")
            table.add_column("Operation", style="yellow")
            table.add_column("Expected", justify="center")
            table.add_column("Actual", justify="center")
            table.add_column("Error", style="red")
            
            for result in failed_results[:10]:  # Limit to first 10 failures
                expected = "Success" if result.expected.success else f"Fail ({result.expected.error_code})"
                
                if result.status == TestResultStatus.ERROR:
                    actual = "ERROR"
                elif result.actual and 'Error' in result.actual:
                    actual = f"Fail ({result.actual['Error'].get('Code', 'Unknown')})"
                else:
                    actual = "Success" if not result.error_message else "Fail"
                
                error_msg = result.error_message or ""
                if len(error_msg) > 50:
                    error_msg = error_msg[:47] + "..."
                
                table.add_row(
                    result.group_name,
                    result.operation_name,
                    expected,
                    actual,
                    error_msg
                )
            
            if len(failed_results) > 10:
                table.add_row("...", f"({len(failed_results) - 10} more failures)", "", "", "")
            
            self.console.print(table)
            self.console.print()
    
    def _display_failures(self, failed_results: List[TestResult]):
        """Display detailed failure information."""
        if not failed_results:
            return
        
        failure_text = Text("Failed Operations:\n", style="bold red")
        
        for result in failed_results[:5]:  # Show first 5 failures
            failure_text.append(f"• {result.group_name} > {result.operation_name}: ")
            
            if result.status == TestResultStatus.ERROR:
                failure_text.append("ERROR", style="red")
            elif result.expected.success:
                failure_text.append("Expected success but failed", style="red")
            else:
                expected_error = result.expected.error_code
                actual_error = result.actual.get('Error', {}).get('Code') if result.actual else 'Unknown'
                failure_text.append(f"Expected {expected_error}, got {actual_error}", style="red")
            
            failure_text.append("\n")
            
            if result.error_message:
                failure_text.append(f"  {result.error_message}\n", style="dim")
        
        if len(failed_results) > 5:
            failure_text.append(f"... and {len(failed_results) - 5} more failures\n")
        
        self.console.print(failure_text)
    
    def _display_session_footer(self, session: TestSession):
        """Display session footer with summary."""
        if not session.summary:
            return
        
        # Overall summary
        total = session.summary.passed + session.summary.failed + session.summary.error
        duration = session.duration or 0.0
        
        summary_text = Text()
        
        if session.summary.failed == 0 and session.summary.error == 0:
            summary_text.append("🎉 All tests passed!\n", style="bold green")
        else:
            summary_text.append("❌ Some tests failed\n", style="bold red")
        
        summary_text.append(f"Total: {total} operations, ")
        summary_text.append(f"{session.summary.passed} passed", style="green")
        summary_text.append(f", {session.summary.failed} failed", style="red")
        
        if session.summary.error > 0:
            summary_text.append(f", {session.summary.error} errors", style="red")
        
        summary_text.append(f"\nDuration: {duration:.2f} seconds")
        
        if duration > 0 and total > 0:
            ops_per_sec = total / duration
            summary_text.append(f" ({ops_per_sec:.1f} ops/sec)")
        
        panel = Panel(summary_text, box=box.ROUNDED, padding=(1, 2))
        self.console.print(panel)
```

### Configuration Loading Integration

**File**: `src/s3tester/cli/config_loader.py`

```python
from pathlib import Path
from typing import Optional
import os
import click
from ..config.models import TestConfiguration

class ConfigLoader:
    """Handle configuration loading with various sources."""
    
    @staticmethod
    def load_configuration(config_path: Optional[Path], 
                          ctx: click.Context) -> TestConfiguration:
        """Load configuration from file with fallbacks."""
        
        # Determine config file path
        final_config_path = ConfigLoader._resolve_config_path(config_path)
        
        if not final_config_path:
            click.echo("Error: Configuration file required.", err=True)
            click.echo("Use --config option or set S3TESTER_CONFIG environment variable.", err=True)
            ctx.exit(2)
        
        if not final_config_path.exists():
            click.echo(f"Error: Configuration file not found: {final_config_path}", err=True)
            ctx.exit(2)
        
        try:
            return TestConfiguration.load_from_file(final_config_path)
        except Exception as e:
            click.echo(f"Error loading configuration: {e}", err=True)
            ctx.exit(2)
    
    @staticmethod
    def _resolve_config_path(explicit_path: Optional[Path]) -> Optional[Path]:
        """Resolve configuration file path from various sources."""
        
        # 1. Explicit command line argument
        if explicit_path:
            return explicit_path.resolve()
        
        # 2. Environment variable
        env_config = os.getenv('S3TESTER_CONFIG')
        if env_config:
            return Path(env_config).resolve()
        
        # 3. Current directory defaults
        default_names = ['s3tester.yaml', 's3tester.yml', 'config.yaml', 'config.yml']
        for name in default_names:
            path = Path.cwd() / name
            if path.exists():
                return path
        
        # 4. User config directory
        user_config_dir = Path.home() / '.config' / 's3tester'
        if user_config_dir.exists():
            for name in default_names:
                path = user_config_dir / name
                if path.exists():
                    return path
        
        return None
```

## Usage Examples

### Basic CLI Usage
```bash
# Run all tests with table output
s3tester --config tests/config.yaml run

# Run specific group with JSON output  
s3tester -c config.yaml --format json run --group "Upload Test"

# Validate configuration in strict mode
s3tester -c config.yaml validate --strict

# List available operations
s3tester list operations

# Dry run all tests
s3tester -c config.yaml --dry-run run
```

### Environment Variable Configuration
```bash
export S3TESTER_CONFIG="path/to/config.yaml"
export S3TESTER_FORMAT="json"
export AWS_PROFILE="testing"

s3tester run --parallel
```

### Programmatic Usage
```python
from s3tester.cli import main
import sys

# Override sys.argv for programmatic usage
sys.argv = ['s3tester', '--config', 'test.yaml', 'run', '--parallel']
main()
```

## Integration Points

### With Core Engine
- CLI passes configuration and options to TestExecutionEngine
- Receives TestSession results for formatting and output
- Handles engine exceptions and converts to appropriate exit codes

### With Configuration Layer  
- Uses TestConfiguration.load_from_file() for config loading
- Integrates ConfigurationValidator for validation
- Supports configuration file discovery and environment variables

### With Reporting Layer
- Uses OutputFormatter for JSON/YAML output
- Uses TableFormatter for Rich console display
- Supports file output for CI/CD integration

## Error Handling

### Exit Codes
- `0`: All tests passed
- `1`: Some tests failed (expected behavior)
- `2`: Configuration error (file not found, validation failed)
- `3`: Runtime error (network issues, unexpected exceptions)
- `130`: Interrupted by user (Ctrl+C)

### Error Display
- Configuration errors: Clear messages with suggestions
- Runtime errors: Context-aware error messages
- Verbose mode: Full stack traces for debugging
- Validation errors: Detailed list with specific issues

## Performance Considerations

1. **Lazy Loading**: Operations and formatters loaded only when needed
2. **Progress Display**: Optional for automated environments
3. **Output Buffering**: Large JSON/YAML output handled efficiently
4. **Memory Management**: Streaming output for large result sets
5. **Signal Handling**: Graceful shutdown on interruption

## Next Steps

The CLI implementation provides:
1. **User-Friendly Interface**: Intuitive commands with help and examples
2. **Flexible Configuration**: Multiple ways to specify configuration
3. **Rich Output**: Beautiful console display with progress tracking
4. **Automation Support**: JSON/YAML output for CI/CD integration
5. **Error Handling**: Comprehensive error reporting with appropriate exit codes
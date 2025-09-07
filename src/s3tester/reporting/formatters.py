"""
Output formatters for s3tester results.
Supports multiple formats: JSON, YAML, Table (text), and Rich console output.
"""
from __future__ import annotations

import json
import sys
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TextIO, Union

import yaml
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.box import SIMPLE

from ..config.models import S3TestResult, S3TestSession


class OutputFormat(Enum):
    """Supported output formats."""
    JSON = auto()
    YAML = auto()
    TABLE = auto()
    CONSOLE = auto()


class OutputFormatter:
    """Base formatter interface."""
    
    def format_session(self, session: S3TestSession, output: Optional[TextIO] = None) -> None:
        """Format and output a complete test session."""
        raise NotImplementedError("Subclasses must implement format_session")
    
    def format_result(self, result: S3TestResult, output: Optional[TextIO] = None) -> None:
        """Format and output a single test result."""
        raise NotImplementedError("Subclasses must implement format_result")


class JsonFormatter(OutputFormatter):
    """Formats test results as JSON."""
    
    def format_session(self, session: S3TestSession, output: Optional[TextIO] = None) -> None:
        """Format test session as JSON."""
        output = output or sys.stdout
        json.dump(
            session.model_dump(mode="json"),
            output,
            indent=2,
            default=str,
        )
        output.write("\n")
    
    def format_result(self, result: S3TestResult, output: Optional[TextIO] = None) -> None:
        """Format a single test result as JSON."""
        output = output or sys.stdout
        json.dump(
            result.model_dump(mode="json"),
            output,
            indent=2,
            default=str,
        )
        output.write("\n")


class YamlFormatter(OutputFormatter):
    """Formats test results as YAML."""
    
    def format_session(self, session: S3TestSession, output: Optional[TextIO] = None) -> None:
        """Format test session as YAML."""
        output = output or sys.stdout
        yaml.safe_dump(
            session.model_dump(mode="json"),
            output,
            default_flow_style=False,
            sort_keys=False,
        )
    
    def format_result(self, result: S3TestResult, output: Optional[TextIO] = None) -> None:
        """Format a single test result as YAML."""
        output = output or sys.stdout
        yaml.safe_dump(
            result.model_dump(mode="json"),
            output,
            default_flow_style=False,
            sort_keys=False,
        )


class TableFormatter(OutputFormatter):
    """Formats test results as ASCII tables."""
    
    def format_session(self, session: S3TestSession, output: Optional[TextIO] = None) -> None:
        """Format test session as an ASCII table."""
        output = output or sys.stdout
        
        # Print session header
        output.write(f"Test Session: {session.session_id}\n")
        output.write(f"Started: {session.start_time}\n")
        output.write(f"Finished: {session.end_time}\n")
        output.write(f"Duration: {session.duration:.2f} seconds\n")
        
        # Print summary
        output.write("Summary:\n")
        output.write("-" * 80 + "\n")
        output.write(f"Total: {session.summary.total}\n")
        output.write(f"Passed: {session.summary.passed}\n")
        output.write(f"Failed: {session.summary.failed}\n")
        output.write(f"Error: {session.summary.error}\n")
        output.write("-" * 80 + "\n\n")
        
        # Print each group's results
        for result in session.results:
            output.write(f"Group: {result.group_name}\n")
            output.write("=" * 80 + "\n")
            output.write(f"{'Operation':<20} {'Status':<10} {'Duration':<10} {'Error':<40}\n")
            output.write("-" * 80 + "\n")
            
            error_msg = result.error_message[:37] + "..." if result.error_message and len(result.error_message) > 40 else result.error_message or ""
            output.write(f"{result.operation_name:<20} {result.status.value:<10} {result.duration:.2f}s {error_msg:<40}\n")
            
            output.write("=" * 80 + "\n\n")
    
    def format_result(self, result: S3TestResult, output: Optional[TextIO] = None) -> None:
        """Format a single test result as an ASCII table."""
        output = output or sys.stdout
        
        output.write(f"Operation: {result.operation_name}\n")
        output.write(f"Status: {result.status.value}\n")
        output.write(f"Duration: {result.duration:.2f} seconds\n")
        
        if result.error_message:
            output.write(f"Error: {result.error_message}\n")
        
        if result.expected:
            output.write("\nExpected Result:\n")
            output.write(f"  Success: {result.expected.success}\n")
            if result.expected.error_code:
                output.write(f"  Error Code: {result.expected.error_code}\n")
        
        if result.actual:
            output.write("\nActual Result:\n")
            for key, value in result.actual.items():
                output.write(f"  {key}: {value}\n")


class RichConsoleFormatter(OutputFormatter):
    """Formats test results using Rich for terminal output."""
    
    def __init__(self) -> None:
        """Initialize with a Rich console."""
        self.console = Console()
    
    def format_session(self, session: S3TestSession, output: Optional[TextIO] = None) -> None:
        """Format test session with Rich styling."""
        # Use standard output or the provided stream
        if output and output != sys.stdout:
            self.console = Console(file=output)
        
        # Session header
        try:
            title = Text(f"Test Session: {session.session_id}", style="bold cyan")
            self.console.rule(title)
            
            started_text = Text()
            started_text.append("Started: ", style="bold")
            started_text.append(str(session.start_time))
            self.console.print(started_text)
            
            finished_text = Text()
            finished_text.append("Finished: ", style="bold")
            finished_text.append(str(session.end_time))
            self.console.print(finished_text)
            
            duration_text = Text()
            duration_text.append("Duration: ", style="bold")
            duration_text.append(f"{session.duration:.2f} seconds")
            self.console.print(duration_text)
            
            # Status based on summary
            success = session.summary.failed == 0 and session.summary.error == 0
            status_value = "SUCCESS" if success else "FAILED"
            status_color = "green" if success else "red"
            text = Text()
            text.append("Status: ", style="bold")
            text.append(status_value, style=status_color)
            self.console.print(text)
            self.console.print()
        except Exception as e:
            error_text = Text(f"Error formatting session header: {e}", style="bold red")
            self.console.print(error_text)
            import traceback
            self.console.print(traceback.format_exc())
        
        # Summary table
        from rich.box import SIMPLE
        summary_table = Table(title="Summary", box=SIMPLE)
        summary_table.add_column("Category", style="cyan")
        summary_table.add_column("Count", style="bold")
        
        summary_table.add_row("Total", str(session.summary.total))
        summary_table.add_row("Passed", Text(str(session.summary.passed), style="green"))
        summary_table.add_row("Failed", Text(str(session.summary.failed), style="red"))
        summary_table.add_row("Error", Text(str(session.summary.error), style="yellow"))
        
        self.console.print(summary_table)
        self.console.print()
        
        # Detailed results by group
        for result in session.results:
            group_title = Text(f"Group: {result.group_name}", style="bold cyan")
            self.console.rule(group_title)
            
            from rich.box import SIMPLE
            result_table = Table(box=SIMPLE)
            result_table.add_column("Operation", style="cyan")
            result_table.add_column("Status", style="bold")
            result_table.add_column("Duration", style="blue")
            result_table.add_column("Error", style="red")
            
            status_style = "green" if result.status.value == "PASS" else "red"
            error_msg = result.error_message[:37] + "..." if result.error_message and len(result.error_message) > 40 else result.error_message or ""
            
            result_table.add_row(
                result.operation_name,
                Text(result.status.value, style=status_style),
                Text(f"{result.duration:.2f}s"),
                error_msg
            )
            
            self.console.print(result_table)
            self.console.print()
    
    def format_result(self, result: S3TestResult, output: Optional[TextIO] = None) -> None:
        """Format a single test result with Rich styling."""
        # Use standard output or the provided stream
        if output and output != sys.stdout:
            self.console = Console(file=output)
        
        # Operation header
        operation_title = Text(f"Operation: {result.operation_name}", style="bold cyan")
        self.console.rule(operation_title)
        
        # Status with color
        status_color = "green" if result.status.value == "PASS" else "red"
        
        status_text = Text()
        status_text.append("Status: ", style="bold")
        status_text.append(result.status.value, style=status_color)
        self.console.print(status_text)
        
        duration_text = Text()
        duration_text.append("Duration: ", style="bold")
        duration_text.append(f"{result.duration:.2f} seconds")
        self.console.print(duration_text)
        
        if result.error_message:
            error_text = Text()
            error_text.append("Error: ", style="bold red")
            error_text.append(result.error_message)
            self.console.print(error_text)
        
        # Expected result table
        if result.expected:
            self.console.print()
            expected_table = Table(title="Expected Result", box=True)
            expected_table.add_column("Field", style="cyan")
            expected_table.add_column("Value")
            
            expected_table.add_row("Success", str(result.expected.success))
            if result.expected.error_code:
                expected_table.add_row("Error Code", result.expected.error_code)
            
            self.console.print(expected_table)
        
        # Actual result table
        if result.actual:
            self.console.print()
            actual_table = Table(title="Actual Result", box=True)
            actual_table.add_column("Field", style="cyan")
            actual_table.add_column("Value")
            
            for key, value in result.actual.items():
                actual_table.add_row(key, str(value))
            
            self.console.print(actual_table)


def get_formatter(format_type: Union[OutputFormat, str]) -> OutputFormatter:
    """Factory function to get the appropriate formatter."""
    if isinstance(format_type, str):
        format_type = format_type.upper()
        try:
            format_type = OutputFormat[format_type]
        except KeyError:
            raise ValueError(f"Unknown output format: {format_type}")
    
    formatters = {
        OutputFormat.JSON: JsonFormatter(),
        OutputFormat.YAML: YamlFormatter(),
        OutputFormat.TABLE: TableFormatter(),
        OutputFormat.CONSOLE: RichConsoleFormatter(),
    }
    
    return formatters.get(format_type, RichConsoleFormatter())

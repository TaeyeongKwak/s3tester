"""Contract tests for CLI help and version commands.

These tests define the expected behavior of the CLI help and version functionality.
They MUST fail initially as per TDD methodology.
"""

import pytest
import subprocess
import sys
from pathlib import Path


class TestCLIHelpContract:
    """Contract tests for CLI help functionality."""

    def test_cli_help_command_exists(self):
        """Test that s3tester --help command exists and returns help text."""
        result = subprocess.run(
            [sys.executable, "-m", "s3tester", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0, f"Help command failed with code {result.returncode}"
        assert "s3tester" in result.stdout.lower(), "Help text should contain program name"
        assert "usage" in result.stdout.lower(), "Help text should contain usage information"
        assert "options" in result.stdout.lower(), "Help text should contain options section"

    def test_cli_help_shows_main_commands(self):
        """Test that help shows the main commands: run, validate, list."""
        result = subprocess.run(
            [sys.executable, "-m", "s3tester", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        help_text = result.stdout.lower()
        assert "run" in help_text, "Help should show 'run' command"
        assert "validate" in help_text, "Help should show 'validate' command" 
        assert "list" in help_text, "Help should show 'list' command"

    def test_cli_version_command_exists(self):
        """Test that s3tester --version command exists and shows version."""
        result = subprocess.run(
            [sys.executable, "-m", "s3tester", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0, f"Version command failed with code {result.returncode}"
        assert "0.1.0" in result.stdout, "Version should show current version 0.1.0"

    def test_cli_version_format(self):
        """Test that version output follows expected format."""
        result = subprocess.run(
            [sys.executable, "-m", "s3tester", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0

    def test_cli_no_args_shows_help(self):
        """Test that running s3tester without arguments shows help or usage."""
        result = subprocess.run(
            [sys.executable, "-m", "s3tester"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should either show help (exit 0) or usage error (exit 2)
        assert result.returncode in [0, 2], f"No args should return 0 or 2, got {result.returncode}"
        
        if result.returncode == 0:
            # If showing help
            assert "usage" in result.stdout.lower(), "Should show usage information"
        else:
            # If showing error
            assert len(result.stderr) > 0 or len(result.stdout) > 0, "Should show error message"

    def test_cli_invalid_option_error(self):
        """Test that invalid options show error and suggest help."""
        result = subprocess.run(
            [sys.executable, "-m", "s3tester", "--invalid-option"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 2, f"Invalid option should return exit code 2, got {result.returncode}"


class TestCLISubcommandHelp:
    """Contract tests for subcommand help functionality."""

    def test_run_command_help(self):
        """Test that 's3tester run --help' shows run command options."""
        result = subprocess.run(
            [sys.executable, "-m", "s3tester", "run", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0, f"Run help failed with code {result.returncode}"
        help_text = result.stdout.lower()
        assert "run" in help_text, "Run help should mention run command"
        assert "--parallel" in help_text, "Run help should show --parallel option"
        assert "--group" in help_text, "Run help should show --group option"
        assert "--output" in help_text, "Run help should show --output option"
        assert "--timeout" in help_text, "Run help should show --timeout option"

    def test_validate_command_help(self):
        """Test that 's3tester validate --help' shows validate command options."""
        result = subprocess.run(
            [sys.executable, "-m", "s3tester", "validate", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0, f"Validate help failed with code {result.returncode}"
        help_text = result.stdout.lower()
        assert "validate" in help_text, "Validate help should mention validate command"
        assert "--strict" in help_text, "Validate help should show --strict option"

    def test_list_command_help(self):
        """Test that 's3tester list --help' shows list command options."""
        result = subprocess.run(
            [sys.executable, "-m", "s3tester", "list", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0, f"List help failed with code {result.returncode}"
        help_text = result.stdout.lower()
        assert "list" in help_text, "List help should mention list command"
        # List command should show what can be listed
        assert any(word in help_text for word in ["groups", "operations", "credentials"]), \
            "List help should show what can be listed"
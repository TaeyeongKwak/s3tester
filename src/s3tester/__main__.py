"""
Main entry point for the s3tester package.
"""
from s3tester.cli_main import main as cli_main

def main() -> None:
    """Entry point for the CLI."""
    cli_main()

if __name__ == "__main__":
    main()

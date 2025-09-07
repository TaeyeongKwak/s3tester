"""S3 API Compatibility Testing Tool (s3tester)

A Python CLI tool for testing S3 API compatibility by executing YAML-defined
test scenarios against S3-compatible storage systems.
"""

__version__ = "0.1.0"
__author__ = "s3tester Development Team"
__description__ = "S3 API compatibility testing tool"

# Export main components
from .config.models import S3TestConfiguration, S3TestSession
from .core.engine import S3TestExecutionEngine
from .cli_main import main

__all__ = [
    "__version__",
    "S3TestConfiguration", 
    "S3TestSession",
    "S3TestExecutionEngine",
    "main"
]
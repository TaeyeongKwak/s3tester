"""S3 API Compatibility Testing Tool (s3tester)

A Python CLI tool for testing S3 API compatibility by executing YAML-defined
test scenarios against S3-compatible storage systems.
"""

__version__ = "0.1.0"
__author__ = "s3tester Development Team"
__description__ = "S3 API compatibility testing tool"

# Export main components
from .config.models import TestConfiguration, TestSession
from .core.engine import TestExecutionEngine
from .cli import main

__all__ = [
    "__version__",
    "TestConfiguration", 
    "TestSession",
    "TestExecutionEngine",
    "main"
]
"""
Command-line interface package for s3tester.

This package provides CLI infrastructure including configuration loading.
"""

# Export the config loader which is used by other modules
from .config_loader import ConfigLoader, ConfigurationLoadError

__all__ = [
    "ConfigLoader",
    "ConfigurationLoadError"
]

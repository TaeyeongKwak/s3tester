"""Configuration constants for s3tester.

This module provides configurable constants that can be overridden
via environment variables for timeouts, retry logic, and other settings.
"""

import os
from typing import Optional


def get_env_int(env_var: str, default: int) -> int:
    """Get integer value from environment variable with fallback to default."""
    try:
        return int(os.getenv(env_var, default))
    except (ValueError, TypeError):
        return default


def get_env_float(env_var: str, default: float) -> float:
    """Get float value from environment variable with fallback to default."""
    try:
        return float(os.getenv(env_var, default))
    except (ValueError, TypeError):
        return default


def get_env_bool(env_var: str, default: bool) -> bool:
    """Get boolean value from environment variable with fallback to default."""
    value = os.getenv(env_var, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


# Environment variable prefix
ENV_PREFIX = "S3TESTER_"

# Timeout Constants
DEFAULT_READ_TIMEOUT = get_env_int(f"{ENV_PREFIX}READ_TIMEOUT", 300)  # 5 minutes
DEFAULT_CONNECT_TIMEOUT = get_env_int(f"{ENV_PREFIX}CONNECT_TIMEOUT", 30)  # 30 seconds

# Retry Constants
DEFAULT_MAX_RETRIES = get_env_int(f"{ENV_PREFIX}MAX_RETRIES", 3)
DEFAULT_BASE_DELAY = get_env_float(f"{ENV_PREFIX}BASE_DELAY", 1.0)  # seconds
DEFAULT_MAX_DELAY = get_env_float(f"{ENV_PREFIX}MAX_DELAY", 60.0)  # seconds
DEFAULT_EXPONENTIAL_FACTOR = get_env_float(f"{ENV_PREFIX}EXPONENTIAL_FACTOR", 2.0)
DEFAULT_RETRY_JITTER = get_env_bool(f"{ENV_PREFIX}RETRY_JITTER", True)

# Default Endpoints
DEFAULT_ENDPOINT_URL = os.getenv(f"{ENV_PREFIX}ENDPOINT_URL", "http://localhost:9000")
DEFAULT_REGION = os.getenv(f"{ENV_PREFIX}REGION", "us-east-1")

# Test Configuration
TEST_BUCKET_PREFIX = os.getenv(f"{ENV_PREFIX}TEST_BUCKET_PREFIX", "s3tester-test")
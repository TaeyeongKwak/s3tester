"""Test utilities for s3tester.

Provides common utilities for tests including dynamic bucket name generation.
"""

import uuid
from s3tester.constants import TEST_BUCKET_PREFIX


def generate_test_bucket_name(prefix: str = None) -> str:
    """Generate a unique test bucket name with UUID suffix.
    
    Args:
        prefix: Optional prefix for bucket name (default: from S3TESTER_TEST_BUCKET_PREFIX)
    
    Returns:
        Unique bucket name in format: {prefix}-{uuid}
    """
    if prefix is None:
        prefix = TEST_BUCKET_PREFIX
    
    # Generate a short UUID to avoid bucket name length limits
    short_uuid = str(uuid.uuid4())[:8]
    return f"{prefix}-{short_uuid}"


def generate_test_key_name(base_name: str = "test-key") -> str:
    """Generate a unique test key name with UUID suffix.
    
    Args:
        base_name: Base name for the key
    
    Returns:
        Unique key name in format: {base_name}-{uuid}
    """
    short_uuid = str(uuid.uuid4())[:8]
    return f"{base_name}-{short_uuid}"
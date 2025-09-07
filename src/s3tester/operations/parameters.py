"""Parameter transformation utilities for S3 operations.

This module provides utilities for transforming configuration parameters
into the format expected by boto3 S3 client.
"""

from pathlib import Path
from typing import Dict, Any, Union
import re
from urllib.parse import quote
from ..config.models import FileReference


class ParameterTransformer:
    """Transform YAML parameters to boto3 format."""
    
    @staticmethod
    def transform_file_reference(value: Union[str, FileReference], 
                               config_dir: Path) -> bytes:
        """Transform file:// reference to file content."""
        import logging
        logger = logging.getLogger("s3tester.parameters")
        
        if isinstance(value, str):
            if value.startswith('file://'):
                logger.debug(f"Processing file reference: {value} with config_dir: {config_dir}")
                file_ref = FileReference.from_path_spec(value, config_dir)
                logger.debug(f"Created FileReference: {file_ref.resolved_path} (exists: {file_ref.exists})")
            else:
                # Treat as literal string content
                return value.encode('utf-8')
        else:
            file_ref = value
        
        if not file_ref.exists:
            error_msg = f"Referenced file not found: {file_ref.resolved_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        logger.debug(f"Reading file content from: {file_ref.resolved_path}")
        return file_ref.read_content()
    
    @staticmethod  
    def transform_bucket_name(bucket: str) -> str:
        """Validate and transform bucket name."""
        # AWS S3 bucket naming rules
        if not re.match(r'^[a-z0-9][a-z0-9.-]*[a-z0-9]$', bucket):
            raise ValueError(f"Invalid bucket name format: {bucket}")
        
        if len(bucket) < 3 or len(bucket) > 63:
            raise ValueError(f"Bucket name length must be 3-63 characters: {bucket}")
            
        if '..' in bucket:
            raise ValueError(f"Bucket name cannot contain consecutive periods: {bucket}")
            
        return bucket
    
    @staticmethod
    def transform_object_key(key: str) -> str:
        """Validate and transform object key."""
        if not key or len(key) > 1024:
            raise ValueError(f"Object key length must be 1-1024 characters: {key}")
        return key
    
    @staticmethod
    def transform_tagging(tags: Dict[str, str]) -> str:
        """Transform tag dictionary to S3 tagging string format."""
        if not tags:
            return ""
        
        tag_pairs = []
        for key, value in tags.items():
            # URL encode key and value
            encoded_key = quote(str(key), safe='')
            encoded_value = quote(str(value), safe='')
            tag_pairs.append(f"{encoded_key}={encoded_value}")
        
        return "&".join(tag_pairs)

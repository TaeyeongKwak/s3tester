import boto3
from botocore.config import Config
from typing import Dict, Any, Optional
from ..config.models import GlobalConfig, CredentialSet
from ..constants import DEFAULT_READ_TIMEOUT, DEFAULT_CONNECT_TIMEOUT
import logging

class S3ClientFactory:
    """Factory for creating configured S3 clients."""
    
    def __init__(self, global_config: Optional[GlobalConfig] = None):
        self.global_config = global_config
        self.logger = logging.getLogger("s3tester.client_factory")
        
        # Client cache for reuse
        self._client_cache: Dict[str, boto3.client] = {}
        
        # Base boto3 configuration
        self.boto_config = Config(
            retries={
                'total_max_attempts': 5,
                'mode': 'standard'
            },
            max_pool_connections=50,  # For high concurrency
            read_timeout=DEFAULT_READ_TIMEOUT,  # Configurable via S3TESTER_READ_TIMEOUT
            connect_timeout=DEFAULT_CONNECT_TIMEOUT  # Configurable via S3TESTER_CONNECT_TIMEOUT
        )
    
    def create_client(self, credential: CredentialSet) -> boto3.client:
        """Create S3 client with specified credentials."""
        cache_key = self._get_cache_key(credential)
        
        if cache_key in self._client_cache:
            return self._client_cache[cache_key]
        
        # Create boto3 session with credentials
        session = boto3.Session(**credential.to_boto3_credentials())
        
        # Create S3 client
        client_kwargs = {
            'service_name': 's3',
            'config': self.boto_config
        }
        
        if self.global_config:
            client_kwargs.update({
                'region_name': self.global_config.region,
                'endpoint_url': self.global_config.endpoint_url,
            })
            
            # Handle path-style addressing - config.path_style 값에 따라 설정
            if self.global_config.path_style:
                client_kwargs['config'] = self.boto_config.merge(
                    Config(s3={'addressing_style': 'path'})
                )
        
        client = session.client(**client_kwargs)
        
        # Cache client for reuse
        self._client_cache[cache_key] = client
        
        endpoint_url = self.global_config.endpoint_url if self.global_config else "default"
        self.logger.debug(
            f"Created S3 client for {credential.name} -> {endpoint_url}"
        )
        
        return client
    
    def _get_cache_key(self, credential: CredentialSet) -> str:
        """Generate cache key for credential set."""
        return f"{credential.name}:{credential.access_key[:8]}"
    
    def clear_cache(self):
        """Clear client cache."""
        self._client_cache.clear()
        self.logger.debug("S3 client cache cleared")
    
    def test_client_connection(self, credential: CredentialSet) -> bool:
        """Test client connection with simple operation."""
        try:
            client = self.create_client(credential)
            
            # Try a simple operation that doesn't require specific permissions
            client.list_buckets()
            return True
            
        except Exception as e:
            self.logger.error(f"Client connection test failed for {credential.name}: {e}")
            return False
            
    def get_client(self, credentials: Dict[str, Any]) -> boto3.client:
        """Get an S3 client instance with the specified credentials dictionary.
        
        This is an alternate interface used by the test suite.
        """
        # Simple implementation for tests
        # Create a new client
        session_args = {}
        
        # Handle access key & secret key
        if "access_key" in credentials and "secret_key" in credentials:
            session_args["aws_access_key_id"] = credentials["access_key"]
            session_args["aws_secret_access_key"] = credentials["secret_key"]
        
        # Handle session token (optional)
        if "session_token" in credentials:
            session_args["aws_session_token"] = credentials["session_token"]
            
        # Handle profile (optional)
        if "profile" in credentials:
            session_args["profile_name"] = credentials["profile"]
            
        # Handle region (required)
        if "region" in credentials:
            session_args["region_name"] = credentials["region"]
            
        # Create session and client
        session = boto3.Session(**session_args)
        
        # Configure client with optional endpoint URL and other settings
        client_args = {}
        
        # Base boto3 configuration
        base_config = Config(
            retries={
                'total_max_attempts': 5,
                'mode': 'standard'
            },
            max_pool_connections=50,
            read_timeout=DEFAULT_READ_TIMEOUT,  # Configurable via S3TESTER_READ_TIMEOUT
            connect_timeout=DEFAULT_CONNECT_TIMEOUT  # Configurable via S3TESTER_CONNECT_TIMEOUT
        )
        
        # path_style 설정에 따라 addressing style 적용
        path_style = credentials.get("path_style")
        if path_style is not None:
            # credentials에서 path_style 값 사용
            if path_style:
                client_args['config'] = base_config.merge(
                    Config(s3={'addressing_style': 'path'})
                )
            else:
                client_args['config'] = base_config.merge(
                    Config(s3={'addressing_style': 'virtual'})
                )
        else:
            # 기본값 설정
            client_args['config'] = base_config
        
        if "endpoint_url" in credentials:
            client_args["endpoint_url"] = credentials["endpoint_url"]
            
        client = session.client('s3', **client_args)
        
        return client

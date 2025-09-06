from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from ..config.models import S3TestConfiguration
from ..operations.registry import OperationRegistry
from .logging_config import get_logger

class ConfigurationValidator:
    """Validate test configuration comprehensively."""
    
    def __init__(self):
        self.logger = get_logger("core.validator")
        
    def validate_configuration(self,
                             config: S3TestConfiguration,
                             strict: bool = False) -> Tuple[bool, List[str]]:
        """Validate configuration comprehensively.
        
        Args:
            config: S3 test configuration to validate
            strict: If True, perform additional validations like file existence and S3 connectivity
            
        Returns:
            Tuple of (is_valid, error_messages) where is_valid is True if configuration is valid,
            and error_messages is a list of human-readable validation error descriptions.
            
        Example:
            >>> validator = ConfigurationValidator()
            >>> is_valid, errors = validator.validate_configuration(config, strict=True)
            >>> if not is_valid:
            ...     for error in errors:
            ...         print(f"❌ {error}")
        """
        errors = []
        
        # Basic structural validation (already done by Pydantic)
        
        # Validate credential references
        errors.extend(self._validate_credential_references(config))
        
        # Validate operations
        errors.extend(self._validate_operations(config))
        
        # Validate file references (if strict mode)
        if strict:
            errors.extend(self._validate_file_references(config))
        
        # Validate S3 connectivity (if strict mode)
        if strict:
            errors.extend(self._validate_s3_connectivity(config))
        
        is_valid = len(errors) == 0
        
        if is_valid:
            self.logger.info("Configuration validation passed")
        else:
            self.logger.error(f"Configuration validation failed with {len(errors)} errors")
            for error in errors:
                self.logger.error(f"  - {error}")
        
        return is_valid, errors
    
    def validate_user_input(self, input_value: str, input_type: str, constraints: Dict[str, Any] = None) -> Tuple[bool, Optional[str]]:
        """Validate user input with clear error messages.
        
        Args:
            input_value: The input value to validate
            input_type: Type of input (e.g., 'bucket_name', 'region', 'endpoint_url')
            constraints: Optional dictionary of constraints to check
            
        Returns:
            Tuple of (is_valid, error_message) where error_message is None if valid
        """
        constraints = constraints or {}
        
        if input_type == 'bucket_name':
            return self._validate_bucket_name(input_value)
        elif input_type == 'region':
            return self._validate_aws_region(input_value)
        elif input_type == 'endpoint_url':
            return self._validate_endpoint_url(input_value)
        elif input_type == 'timeout':
            return self._validate_timeout(input_value, constraints.get('min', 1), constraints.get('max', 3600))
        elif input_type == 'file_path':
            return self._validate_file_path(input_value, constraints.get('must_exist', True))
        else:
            return True, None
    
    def _validate_bucket_name(self, bucket_name: str) -> Tuple[bool, Optional[str]]:
        """Validate S3 bucket name according to AWS rules."""
        if not bucket_name:
            return False, "Bucket name cannot be empty"
            
        if len(bucket_name) < 3:
            return False, f"Bucket name '{bucket_name}' is too short (minimum 3 characters)"
            
        if len(bucket_name) > 63:
            return False, f"Bucket name '{bucket_name}' is too long (maximum 63 characters)"
            
        if not bucket_name.replace('-', '').replace('.', '').isalnum():
            return False, f"Bucket name '{bucket_name}' contains invalid characters (only letters, numbers, hyphens, and periods allowed)"
            
        if bucket_name.startswith('-') or bucket_name.endswith('-'):
            return False, f"Bucket name '{bucket_name}' cannot start or end with hyphens"
            
        if '..' in bucket_name:
            return False, f"Bucket name '{bucket_name}' cannot contain consecutive periods"
            
        import re
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', bucket_name):
            return False, f"Bucket name '{bucket_name}' cannot be an IP address"
            
        return True, None
    
    def _validate_aws_region(self, region: str) -> Tuple[bool, Optional[str]]:
        """Validate AWS region name."""
        if not region:
            return False, "Region cannot be empty"
            
        valid_regions = {
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1',
            'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2',
            'sa-east-1', 'ca-central-1', 'ap-south-1'
        }
        
        if region not in valid_regions and not region.startswith('us-gov-'):
            return False, f"Region '{region}' is not a recognized AWS region. Common regions: {', '.join(sorted(valid_regions)[:5])}, ..."
            
        return True, None
    
    def _validate_endpoint_url(self, endpoint_url: str) -> Tuple[bool, Optional[str]]:
        """Validate endpoint URL format."""
        if not endpoint_url:
            return False, "Endpoint URL cannot be empty"
            
        if not endpoint_url.startswith(('http://', 'https://')):
            return False, f"Endpoint URL '{endpoint_url}' must start with 'http://' or 'https://'"
            
        try:
            from urllib.parse import urlparse
            parsed = urlparse(endpoint_url)
            if not parsed.netloc:
                return False, f"Endpoint URL '{endpoint_url}' is missing hostname"
        except Exception as e:
            return False, f"Invalid endpoint URL '{endpoint_url}': {e}"
            
        return True, None
    
    def _validate_timeout(self, timeout_str: str, min_value: int = 1, max_value: int = 3600) -> Tuple[bool, Optional[str]]:
        """Validate timeout value."""
        try:
            timeout = int(timeout_str)
        except ValueError:
            return False, f"Timeout '{timeout_str}' must be a valid integer"
            
        if timeout < min_value:
            return False, f"Timeout {timeout} is too small (minimum {min_value} seconds)"
            
        if timeout > max_value:
            return False, f"Timeout {timeout} is too large (maximum {max_value} seconds)"
            
        return True, None
    
    def _validate_file_path(self, file_path: str, must_exist: bool = True) -> Tuple[bool, Optional[str]]:
        """Validate file path."""
        if not file_path:
            return False, "File path cannot be empty"
            
        from pathlib import Path
        try:
            path = Path(file_path)
            if must_exist and not path.exists():
                return False, f"File '{file_path}' does not exist"
            if must_exist and not path.is_file():
                return False, f"Path '{file_path}' exists but is not a file"
        except Exception as e:
            return False, f"Invalid file path '{file_path}': {e}"
            
        return True, None
    
    def _validate_credential_references(self, config: S3TestConfiguration) -> List[str]:
        """Validate all credential references exist."""
        errors = []
        credential_names = {cred.name for cred in config.config.credentials}
        
        # Check group credential references
        for group in config.test_cases.groups:
            if group.credential not in credential_names:
                errors.append(f"Group '{group.name}' references unknown credential '{group.credential}'")
        
        # Check operation credential overrides
        for group in config.test_cases.groups:
            for phase, operations in [
                ("before_test", group.before_test),
                ("test", group.test),
                ("after_test", group.after_test)
            ]:
                for op in operations:
                    if op.credential and op.credential not in credential_names:
                        errors.append(
                            f"Operation '{op.operation}' in group '{group.name}' "
                            f"references unknown credential '{op.credential}'"
                        )
        
        return errors
    
    def _validate_operations(self, config: S3TestConfiguration) -> List[str]:
        """Validate all operations are supported."""
        errors = []
        supported_ops = set(OperationRegistry.list_operations())
        
        for group in config.test_cases.groups:
            for phase, operations in [
                ("before_test", group.before_test),
                ("test", group.test),
                ("after_test", group.after_test)
            ]:
                for op in operations:
                    if op.operation not in supported_ops:
                        errors.append(
                            f"Unsupported operation '{op.operation}' in group '{group.name}'"
                        )
        
        return errors
    
    def _validate_file_references(self, config: S3TestConfiguration) -> List[str]:
        """Validate all file:// references exist."""
        errors = []
        config_dir = config.config_file_path.parent if config.config_file_path else Path.cwd()
        
        for group in config.test_cases.groups:
            for phase, operations in [
                ("before_test", group.before_test),
                ("test", group.test),
                ("after_test", group.after_test)
            ]:
                for op in operations:
                    for param_name, param_value in op.parameters.items():
                        if isinstance(param_value, str) and param_value.startswith('file://'):
                            try:
                                from ..config.models import FileReference
                                file_ref = FileReference.from_path_spec(param_value, config_dir)
                                if not file_ref.exists:
                                    errors.append(
                                        f"File not found: {file_ref.resolved_path} "
                                        f"(referenced in {group.name}:{op.operation}:{param_name})"
                                    )
                            except Exception as e:
                                errors.append(
                                    f"Invalid file reference '{param_value}' "
                                    f"in {group.name}:{op.operation}:{param_name}: {e}"
                                )
        
        return errors
    
    def _validate_s3_connectivity(self, config: S3TestConfiguration) -> List[str]:
        """Test S3 connectivity for all credentials."""
        errors = []
        
        from .client_factory import S3ClientFactory
        client_factory = S3ClientFactory(config.config)
        
        for credential in config.config.credentials:
            try:
                if not client_factory.test_client_connection(credential):
                    errors.append(f"Cannot connect to S3 with credential '{credential.name}'")
            except Exception as e:
                errors.append(f"S3 connectivity test failed for '{credential.name}': {e}")
        
        return errors

"""Data models for s3tester configuration.

This module defines the Pydantic models used for configuration validation,
parsing, and handling of S3 test configurations.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum
from urllib.parse import urlparse
import yaml
import re
import os
from datetime import datetime


class S3TestConfiguration(BaseModel):
    """Primary configuration container for s3tester."""
    
    config: 'GlobalConfig'
    test_cases: 'S3TestCases'
    include: Optional[List[Path]] = Field(default_factory=list)
    
    # Internal fields for processing
    config_file_path: Optional[Path] = Field(default=None, exclude=True)
    
    @field_validator('include')
    @classmethod
    def validate_included_files(cls, v: List[Path]) -> List[Path]:
        """Validate that all included files exist and are readable."""
        for file_path in v:
            if not file_path.exists():
                raise ValueError(f"Include file not found: {file_path}")
            if not file_path.is_file():
                raise ValueError(f"Include path is not a file: {file_path}")
        return v
    
    @classmethod
    def load_from_file(cls, config_path: Path) -> 'S3TestConfiguration':
        """Load configuration from YAML file with include processing."""
        config_path = config_path.resolve()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
        
        # Substitute environment variables
        yaml_content = cls._substitute_env_vars(yaml_content)
        
        raw_data = yaml.safe_load(yaml_content)
        
        # Process includes
        if 'include' in raw_data:
            included_configs = []
            for include_path in raw_data['include']:
                if isinstance(include_path, str):
                    # Resolve relative to config file directory
                    include_path = config_path.parent / include_path
                included_configs.append(cls.load_from_file(include_path))
            
            # Merge included configurations (current file takes precedence)
            raw_data = cls._merge_configurations(included_configs, raw_data)
        
        config = cls(**raw_data)
        config.config_file_path = config_path
        return config
    
    @staticmethod
    def _substitute_env_vars(yaml_content: str) -> str:
        """Substitute environment variables in YAML content.
        
        Supports syntax: ${ENV_VAR} and ${ENV_VAR:-default_value}
        """
        def replace_env_var(match):
            var_expr = match.group(1)
            
            # Check if it has default value syntax
            if ':-' in var_expr:
                var_name, default_value = var_expr.split(':-', 1)
                return os.getenv(var_name.strip(), default_value.strip())
            else:
                var_name = var_expr.strip()
                return os.getenv(var_name, f"${{{var_name}}}")  # Keep original if not found
        
        # Pattern to match ${VAR} or ${VAR:-default}
        pattern = r'\$\{([^}]+)\}'
        return re.sub(pattern, replace_env_var, yaml_content)
    
    @staticmethod
    def _merge_configurations(included_configs: List['S3TestConfiguration'], 
                            current_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration objects with precedence rules."""
        # Implementation for configuration merging
        # Current file > Included files (in reverse order)
        merged = {}
        
        # Start with included configs
        for config in included_configs:
            config_dict = config.model_dump(exclude={'config_file_path'})
            merged = S3TestConfiguration._deep_merge(merged, config_dict)
        
        # Apply current config (highest precedence)
        merged = S3TestConfiguration._deep_merge(merged, current_config)
        return merged
    
    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = S3TestConfiguration._deep_merge(result[key], value)
            else:
                result[key] = value
        return result


class GlobalConfig(BaseModel):
    """Global configuration settings for S3 service connection."""
    
    endpoint_url: str = Field(..., description="S3-compatible service endpoint URL")
    region: str = Field(default="us-east-1", description="AWS region identifier")
    path_style: bool = Field(default=False, description="Use path-style URLs")
    credentials: List['CredentialSet'] = Field(..., min_length=1)
    
    @field_validator('endpoint_url')
    @classmethod
    def validate_endpoint_url(cls, v: str) -> str:
        """Validate endpoint URL format."""
        parsed = urlparse(v)
        if not parsed.scheme or parsed.scheme not in ['http', 'https']:
            raise ValueError(f"Invalid endpoint URL scheme: {v}")
        if not parsed.netloc:
            raise ValueError(f"Invalid endpoint URL format: {v}")
        return v
    
    @field_validator('region')
    @classmethod
    def validate_region(cls, v: str) -> str:
        """Validate AWS region format."""
        import re
        if not re.match(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$', v):
            raise ValueError(f"Invalid AWS region format: {v}")
        return v
    
    @model_validator(mode='after')
    def validate_credential_names_unique(self) -> 'GlobalConfig':
        """Ensure all credential names are unique."""
        names = [cred.name for cred in self.credentials]
        if len(names) != len(set(names)):
            raise ValueError("Credential names must be unique")
        return self
    
    def get_credential(self, name: str) -> Optional['CredentialSet']:
        """Get credential set by name."""
        for cred in self.credentials:
            if cred.name == name:
                return cred
        return None


class CredentialSet(BaseModel):
    """Named authentication credentials for S3 operations."""
    
    name: str = Field(..., min_length=1, description="Unique identifier")
    access_key: str = Field(..., min_length=1, description="AWS access key ID")
    secret_key: str = Field(..., min_length=1, description="AWS secret access key")
    session_token: Optional[str] = Field(default=None, description="Session token for temporary credentials")
    
    @field_validator('name')
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Validate credential name contains only safe characters."""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(f"Credential name contains invalid characters: {v}")
        return v
    
    def to_boto3_credentials(self) -> Dict[str, str]:
        """Convert to boto3 session credentials format."""
        creds = {
            'aws_access_key_id': self.access_key,
            'aws_secret_access_key': self.secret_key
        }
        if self.session_token:
            creds['aws_session_token'] = self.session_token
        return creds


class S3TestGroupStatus(str, Enum):
    """Status values for test group execution."""
    PENDING = "pending"
    RUNNING_BEFORE = "running_before"
    RUNNING_TEST = "running_test"
    RUNNING_AFTER = "running_after"
    COMPLETED = "completed"
    FAILED = "failed"


class S3TestGroup(BaseModel):
    """Collection of related test operations."""
    
    name: str = Field(..., min_length=1)
    credential: str = Field(..., min_length=1, description="Credential set name")
    before_test: List['Operation'] = Field(default_factory=list)
    test: List['Operation'] = Field(..., min_length=1)
    after_test: List['Operation'] = Field(default_factory=list)
    
    # Runtime state (not serialized)
    status_internal: S3TestGroupStatus = Field(default=S3TestGroupStatus.PENDING, exclude=True)
    start_time_internal: Optional[float] = Field(default=None, exclude=True)
    end_time_internal: Optional[float] = Field(default=None, exclude=True)
    
    @model_validator(mode='after')
    def validate_credential_reference(self) -> 'S3TestGroup':
        """Validate credential reference will be checked at runtime."""
        # Note: Actual credential validation happens during execution
        # when we have access to the full configuration
        return self
    
    def get_all_operations(self) -> List['Operation']:
        """Get all operations in execution order."""
        return self.before_test + self.test + self.after_test
    
    def set_status(self, status: S3TestGroupStatus):
        """Update execution status."""
        import time
        self.status_internal = status
        if status == S3TestGroupStatus.RUNNING_BEFORE and not self.start_time_internal:
            self.start_time_internal = time.time()
        elif status in [S3TestGroupStatus.COMPLETED, S3TestGroupStatus.FAILED]:
            self.end_time_internal = time.time()
    
    @property
    def duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.start_time_internal and self.end_time_internal:
            return self.end_time_internal - self.start_time_internal
        return None


class S3TestCases(BaseModel):
    """Test execution configuration container."""
    
    parallel: bool = Field(default=False, description="Execute groups in parallel")
    groups: List[S3TestGroup] = Field(..., min_length=1)
    
    @model_validator(mode='after')
    def validate_group_names_unique(self) -> 'S3TestCases':
        """Ensure all test group names are unique."""
        names = [group.name for group in self.groups]
        if len(names) != len(set(names)):
            raise ValueError("Test group names must be unique")
        return self
    
    def get_group(self, name: str) -> Optional[S3TestGroup]:
        """Get test group by name."""
        for group in self.groups:
            if group.name == name:
                return group
        return None


class ExpectedResult(BaseModel):
    """Expected operation outcome for validation."""
    
    success: bool = Field(default=True, description="Whether operation should succeed")
    error_code: Optional[str] = Field(default=None, description="Expected S3 error code")
    response_contains: Optional['ResponseValidation'] = Field(default=None)
    
    @model_validator(mode='after')
    def validate_error_code_required_for_failure(self) -> 'ExpectedResult':
        """Require error_code when success=False."""
        if not self.success and not self.error_code:
            raise ValueError("error_code required when success=False")
        if self.success and self.error_code:
            raise ValueError("error_code should not be specified when success=True")
        return self
    
    @field_validator('error_code')
    @classmethod
    def validate_error_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate S3 error code format."""
        if v is None:
            return v
        
        # Common S3 error codes
        VALID_ERROR_CODES = {
            'AccessDenied', 'BucketAlreadyExists', 'BucketAlreadyOwnedByYou',
            'BucketNotEmpty', 'InvalidBucketName', 'NoSuchBucket', 'NoSuchKey',
            'InvalidRequest', 'MalformedPolicy', 'PolicyTooLarge',
            'MethodNotAllowed', 'PreconditionFailed', 'RequestTimeout',
            'ServiceUnavailable', 'SlowDown', 'InternalError',
            'InvalidAccessKeyId', 'InvalidSecurity', 'SignatureDoesNotMatch',
            'TokenRefreshRequired', 'InvalidToken', 'MissingSecurityHeader'
        }
        
        if v not in VALID_ERROR_CODES:
            # Warning rather than error for extensibility
            import warnings
            warnings.warn(f"Unknown S3 error code: {v}")
        
        return v


class ResponseValidation(BaseModel):
    """Optional response content validation."""
    
    headers: Optional[Dict[str, str]] = Field(default=None)
    body_pattern: Optional[str] = Field(default=None, description="Regex pattern")
    metadata: Optional[Dict[str, str]] = Field(default=None)
    
    @field_validator('body_pattern')
    @classmethod
    def validate_regex_pattern(cls, v: Optional[str]) -> Optional[str]:
        """Validate regex pattern syntax."""
        if v is not None:
            import re
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")
        return v


class Operation(BaseModel):
    """Individual S3 API operation definition."""
    
    operation: str = Field(..., description="S3 operation name")
    credential: Optional[str] = Field(default=None, description="Override credential")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")
    expected_result: ExpectedResult = Field(default_factory=ExpectedResult, description="Expected outcome")
    
    # Runtime state
    result_internal: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    
    @field_validator('operation')
    @classmethod
    def validate_operation_name(cls, v: str) -> str:
        """Validate operation name against supported operations."""
        # Import here to avoid circular imports
        try:
            from ..operations.registry import OperationRegistry
            supported_operations = OperationRegistry.list_operations()
            
            if v not in supported_operations:
                raise ValueError(f"Unsupported operation: {v}. Supported operations: {', '.join(sorted(supported_operations))}")
        except ImportError:
            # If registry is not available, skip validation
            pass
        
        return v
    
    @field_validator('parameters')
    @classmethod
    def validate_parameters(cls, v: Dict[str, Any], info) -> Dict[str, Any]:
        """Validate parameters based on operation type."""
        # Basic validation - operation-specific validation happens at execution
        if not isinstance(v, dict):
            raise ValueError("Parameters must be a dictionary")
        return v
    
    def resolve_file_paths(self, config_path: Path) -> 'Operation':
        """Resolve file:// paths relative to config file."""
        resolved_params = self.parameters.copy()
        
        for key, value in resolved_params.items():
            if isinstance(value, str) and value.startswith('file://'):
                file_ref = FileReference.from_path_spec(value, config_path.parent)
                resolved_params[key] = file_ref
        
        return self.model_copy(update={'parameters': resolved_params})


class FileReference(BaseModel):
    """Handle file:// path references in configuration."""
    
    raw_path: str = Field(..., description="Original path specification")
    resolved_path: Path = Field(..., description="Absolute resolved path")
    exists: bool = Field(..., description="File existence at resolution time")
    
    @classmethod
    def from_path_spec(cls, path_spec: str, base_dir: Path) -> 'FileReference':
        """Create FileReference from path specification."""
        if path_spec.startswith('file://'):
            # Parse file:// URL
            from urllib.parse import urlparse, unquote
            
            # 디버깅 로그 추가
            import logging
            logger = logging.getLogger("s3tester.file")
            logger.debug(f"Parsing file:// URL: {path_spec} with base_dir: {base_dir}")
            
            # 기존 URL 파싱
            parsed = urlparse(path_spec)
            file_path_str = unquote(parsed.path)
            logger.debug(f"Parsed path: {file_path_str}")
            
            # 파일 경로에서 'file://' 프로토콜을 제거하고 직접 처리
            clean_path = path_spec.replace('file://', '')
            logger.debug(f"Clean path: {clean_path}")
            
            # 단순 경로 사용
            file_path = Path(clean_path)
            logger.debug(f"Initial path: {file_path}")
        else:
            file_path = Path(path_spec)
        
        # Resolve relative to base directory
        if not file_path.is_absolute():
            file_path = base_dir / file_path
            import logging
            logger = logging.getLogger("s3tester.file")
            logger.debug(f"Resolved relative path: {file_path}")
        
        resolved_path = file_path.resolve()
        
        return cls(
            raw_path=path_spec,
            resolved_path=resolved_path,
            exists=resolved_path.exists()
        )
    
    def read_content(self) -> bytes:
        """Read file content as bytes."""
        if not self.exists:
            raise FileNotFoundError(f"File not found: {self.resolved_path}")
        
        return self.resolved_path.read_bytes()
    
    def read_text(self, encoding: str = 'utf-8') -> str:
        """Read file content as text."""
        if not self.exists:
            raise FileNotFoundError(f"File not found: {self.resolved_path}")
        
        return self.resolved_path.read_text(encoding=encoding)


class S3TestResultStatus(str, Enum):
    """Status values for test results."""
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


class S3TestResult(BaseModel):
    """Result of individual operation execution."""
    
    operation_name: str
    group_name: str
    status: S3TestResultStatus = Field(default=S3TestResultStatus.PENDING)
    duration: float = Field(default=0.0, ge=0)
    expected: ExpectedResult
    actual: Optional[Dict[str, Any]] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    extras: Dict[str, Any] = Field(default_factory=dict)  # 추가 메타데이터를 위한 필드
    
    # Phase information for better error reporting
    phase_name: Optional[str] = Field(default=None, description="Phase name: before_test, test, or after_test")
    phase_index: Optional[int] = Field(default=None, description="1-based index within the phase")
    phase_total: Optional[int] = Field(default=None, description="Total operations in this phase")
    
    def set_result(self, success: bool, duration: float, 
                   actual_response: Optional[Dict[str, Any]] = None,
                   error_message: Optional[str] = None):
        """Update result based on operation execution."""
        self.duration = duration
        self.actual = actual_response
        
        # Store error message for reference but don't automatically set ERROR status
        if error_message:
            self.error_message = error_message
        
        # Determine status based on expectation matching
        if self._matches_expected(success, actual_response):
            self.status = S3TestResultStatus.PASS
        else:
            self.status = S3TestResultStatus.FAIL
    
    def _matches_expected(self, actual_success: bool, 
                         actual_response: Optional[Dict[str, Any]]) -> bool:
        """Check if actual result matches expected result."""
        import logging
        logger = logging.getLogger("s3tester.result")
        
        # 디버깅을 위한 정보 로깅
        logger.debug(f"[{self.operation_name}] Comparing expected result: "
                   f"(success={self.expected.success}, error_code={self.expected.error_code}) "
                   f"vs actual result: (success={actual_success}, response_keys={list(actual_response.keys()) if actual_response else None})")
        
        # Basic success/failure match
        if actual_success != self.expected.success:
            if self.expected.success:
                # 성공 예상했지만 실패함
                if actual_response and 'Error' in actual_response:
                    error_code = actual_response.get('Error', {}).get('Code', 'Unknown')
                    error_msg = actual_response.get('Error', {}).get('Message', 'Unknown error')
                    self.error_message = f"{error_code} - {error_msg}"
                    logger.debug(f"[{self.operation_name}] Expected success but got error: {error_code} - {error_msg}")
                else:
                    self.error_message = "Failed with unknown error"
                    logger.debug(f"[{self.operation_name}] Expected success but failed with unknown error")
            else:
                # 실패 예상했지만 성공함
                self.error_message = f"Expected failure but operation succeeded"
                logger.debug(f"[{self.operation_name}] Expected failure but operation succeeded")
            return False
        
        # Success case - 성공 예상하고 성공함
        if self.expected.success and actual_success:
            logger.debug(f"[{self.operation_name}] Success match: expected=True, actual=True")
            # Additional response validation (if specified)
            if self.expected.response_contains and actual_response:
                result = self._validate_response_contains(actual_response)
                if not result:
                    self.error_message = "Response validation failed"
                    logger.debug(f"[{self.operation_name}] Response validation failed")
                    return False
                else:
                    logger.debug(f"[{self.operation_name}] Response validation passed")
            else:
                logger.debug(f"[{self.operation_name}] No response validation required")
            return True
        
        # Failure case - 실패 예상하고 실패함
        if not self.expected.success and not actual_success:
            logger.debug(f"[{self.operation_name}] Failure match: expected=False, actual=False")
            
            # Check error code if specified
            if self.expected.error_code:
                actual_error_code = actual_response.get('Error', {}).get('Code') if actual_response else None
                if actual_error_code != self.expected.error_code:
                    expected_code = self.expected.error_code
                    self.error_message = f"Expected error code {expected_code} but got {actual_error_code}"
                    logger.debug(f"[{self.operation_name}] Error code mismatch: expected {expected_code}, got {actual_error_code}")
                    return False
                else:
                    logger.debug(f"[{self.operation_name}] Error code match: expected={self.expected.error_code}, actual={actual_error_code}")
            else:
                logger.debug(f"[{self.operation_name}] No specific error code expected")
            
            return True
        
        # Should not reach here, but just in case
        logger.warning(f"[{self.operation_name}] Unexpected comparison state: expected.success={self.expected.success}, actual_success={actual_success}")
        return True
    
    def _validate_response_contains(self, response: Dict[str, Any]) -> bool:
        """Validate response contains expected content."""
        validation = self.expected.response_contains
        
        if validation.headers:
            response_headers = response.get('ResponseMetadata', {}).get('HTTPHeaders', {})
            for key, expected_value in validation.headers.items():
                if response_headers.get(key.lower()) != expected_value:
                    return False
        
        if validation.body_pattern and 'Body' in response:
            import re
            body_content = str(response['Body'])
            if not re.search(validation.body_pattern, body_content):
                return False
        
        if validation.metadata:
            response_metadata = response.get('Metadata', {})
            for key, expected_value in validation.metadata.items():
                if response_metadata.get(key) != expected_value:
                    return False
        
        return True


class S3TestSummary(BaseModel):
    """Aggregated test results summary."""
    
    passed: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    error: int = Field(default=0, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @property
    def total(self) -> int:
        """Get total number of test operations."""
        return self.passed + self.failed + self.error
    
    @classmethod
    def from_results(cls, results: List[S3TestResult]) -> 'S3TestSummary':
        """Generate summary from result list."""
        passed = sum(1 for r in results if r.status == S3TestResultStatus.PASS)
        failed = sum(1 for r in results if r.status == S3TestResultStatus.FAIL)
        error = sum(1 for r in results if r.status == S3TestResultStatus.ERROR)
        total = len(results)
        
        success_rate = passed / total if total > 0 else 0.0
        
        return cls(
            passed=passed,
            failed=failed,
            error=error,
            success_rate=success_rate
        )


class S3TestSession(BaseModel):
    """Complete test execution session."""
    
    session_id: str = Field(..., description="Unique session identifier")
    config_file: Path
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = Field(default=None)
    total_operations: int = Field(default=0)
    results: List[S3TestResult] = Field(default_factory=list)
    summary: Optional[S3TestSummary] = Field(default=None)
    
    def add_result(self, result: S3TestResult):
        """Add operation result to session."""
        self.results.append(result)
        self.total_operations = len(self.results)
    
    def finalize(self):
        """Finalize session and generate summary."""
        self.end_time = datetime.utcnow()
        self.summary = S3TestSummary.from_results(self.results)
    
    @property
    def duration(self) -> Optional[float]:
        """Session duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


# Initialize forward references to handle circular references
S3TestConfiguration.model_rebuild()
GlobalConfig.model_rebuild()
S3TestGroup.model_rebuild()
Operation.model_rebuild()
S3TestResult.model_rebuild()
S3TestSession.model_rebuild()

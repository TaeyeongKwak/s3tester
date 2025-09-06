# Data Model Implementation Guide

## Complete Pydantic Model Implementations

### Core Configuration Models

#### TestConfiguration
**File**: `src/s3tester/config/models.py`

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import yaml

class TestConfiguration(BaseModel):
    """Primary configuration container for s3tester."""
    
    config: 'GlobalConfig'
    test_cases: 'TestCases'
    include: Optional[List[Path]] = Field(default_factory=list)
    
    # Internal fields for processing
    _config_file_path: Optional[Path] = Field(default=None, exclude=True)
    
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
    def load_from_file(cls, config_path: Path) -> 'TestConfiguration':
        """Load configuration from YAML file with include processing."""
        config_path = config_path.resolve()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_data = yaml.safe_load(f)
        
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
        config._config_file_path = config_path
        return config
    
    @staticmethod
    def _merge_configurations(included_configs: List['TestConfiguration'], 
                            current_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration objects with precedence rules."""
        # Implementation for configuration merging
        # Current file > Included files (in reverse order)
        merged = {}
        
        # Start with included configs
        for config in included_configs:
            config_dict = config.model_dump(exclude={'_config_file_path'})
            merged = cls._deep_merge(merged, config_dict)
        
        # Apply current config (highest precedence)
        merged = cls._deep_merge(merged, current_config)
        return merged
    
    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = TestConfiguration._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
```

#### GlobalConfig
```python
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
```

#### CredentialSet
```python
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
```

### Test Definition Models

#### TestCases
```python
class TestCases(BaseModel):
    """Test execution configuration container."""
    
    parallel: bool = Field(default=False, description="Execute groups in parallel")
    groups: List['TestGroup'] = Field(..., min_length=1)
    
    @model_validator(mode='after')
    def validate_group_names_unique(self) -> 'TestCases':
        """Ensure all test group names are unique."""
        names = [group.name for group in self.groups]
        if len(names) != len(set(names)):
            raise ValueError("Test group names must be unique")
        return self
    
    def get_group(self, name: str) -> Optional['TestGroup']:
        """Get test group by name."""
        for group in self.groups:
            if group.name == name:
                return group
        return None
```

#### TestGroup
```python
from enum import Enum

class TestGroupStatus(str, Enum):
    PENDING = "pending"
    RUNNING_BEFORE = "running_before"
    RUNNING_TEST = "running_test"
    RUNNING_AFTER = "running_after"
    COMPLETED = "completed"
    FAILED = "failed"

class TestGroup(BaseModel):
    """Collection of related test operations."""
    
    name: str = Field(..., min_length=1)
    credential: str = Field(..., min_length=1, description="Credential set name")
    before_test: List['Operation'] = Field(default_factory=list)
    test: List['Operation'] = Field(..., min_length=1)
    after_test: List['Operation'] = Field(default_factory=list)
    
    # Runtime state (not serialized)
    _status: TestGroupStatus = Field(default=TestGroupStatus.PENDING, exclude=True)
    _start_time: Optional[float] = Field(default=None, exclude=True)
    _end_time: Optional[float] = Field(default=None, exclude=True)
    
    @model_validator(mode='after')
    def validate_credential_reference(self) -> 'TestGroup':
        """Validate credential reference will be checked at runtime."""
        # Note: Actual credential validation happens during execution
        # when we have access to the full configuration
        return self
    
    def get_all_operations(self) -> List['Operation']:
        """Get all operations in execution order."""
        return self.before_test + self.test + self.after_test
    
    def set_status(self, status: TestGroupStatus):
        """Update execution status."""
        import time
        self._status = status
        if status == TestGroupStatus.RUNNING_BEFORE and not self._start_time:
            self._start_time = time.time()
        elif status in [TestGroupStatus.COMPLETED, TestGroupStatus.FAILED]:
            self._end_time = time.time()
    
    @property
    def duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self._start_time and self._end_time:
            return self._end_time - self._start_time
        return None
```

#### Operation
```python
from typing import Union

class Operation(BaseModel):
    """Individual S3 API operation definition."""
    
    operation: str = Field(..., description="S3 operation name")
    credential: Optional[str] = Field(default=None, description="Override credential")
    parameters: Dict[str, Any] = Field(..., description="Operation parameters")
    expected_result: 'ExpectedResult' = Field(..., description="Expected outcome")
    
    # Runtime state
    _result: Optional['OperationResult'] = Field(default=None, exclude=True)
    
    @field_validator('operation')
    @classmethod
    def validate_operation_name(cls, v: str) -> str:
        """Validate operation name against supported operations."""
        # Import here to avoid circular imports
        from .operations import SUPPORTED_OPERATIONS
        if v not in SUPPORTED_OPERATIONS:
            raise ValueError(f"Unsupported operation: {v}")
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
```

#### ExpectedResult
```python
class ExpectedResult(BaseModel):
    """Expected operation outcome for validation."""
    
    success: bool = Field(..., description="Whether operation should succeed")
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
```

### Execution Result Models

#### TestResult
```python
from datetime import datetime
from enum import Enum

class TestResultStatus(str, Enum):
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"

class TestResult(BaseModel):
    """Result of individual operation execution."""
    
    operation_name: str
    group_name: str
    status: TestResultStatus = Field(default=TestResultStatus.PENDING)
    duration: float = Field(default=0.0, ge=0)
    expected: ExpectedResult
    actual: Optional[Dict[str, Any]] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def set_result(self, success: bool, duration: float, 
                   actual_response: Optional[Dict[str, Any]] = None,
                   error_message: Optional[str] = None):
        """Update result based on operation execution."""
        self.duration = duration
        self.actual = actual_response
        self.error_message = error_message
        
        if error_message:
            self.status = TestResultStatus.ERROR
        elif self._matches_expected(success, actual_response):
            self.status = TestResultStatus.PASS
        else:
            self.status = TestResultStatus.FAIL
    
    def _matches_expected(self, actual_success: bool, 
                         actual_response: Optional[Dict[str, Any]]) -> bool:
        """Check if actual result matches expected result."""
        # Basic success/failure match
        if actual_success != self.expected.success:
            return False
        
        # If expecting failure, check error code
        if not self.expected.success and self.expected.error_code:
            actual_error_code = actual_response.get('Error', {}).get('Code') if actual_response else None
            if actual_error_code != self.expected.error_code:
                return False
        
        # Additional response validation
        if self.expected.response_contains and actual_response:
            return self._validate_response_contains(actual_response)
        
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

class TestSession(BaseModel):
    """Complete test execution session."""
    
    session_id: str = Field(..., description="Unique session identifier")
    config_file: Path
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = Field(default=None)
    total_operations: int = Field(default=0)
    results: List[TestResult] = Field(default_factory=list)
    summary: Optional['TestSummary'] = Field(default=None)
    
    def add_result(self, result: TestResult):
        """Add operation result to session."""
        self.results.append(result)
        self.total_operations = len(self.results)
    
    def finalize(self):
        """Finalize session and generate summary."""
        self.end_time = datetime.utcnow()
        self.summary = TestSummary.from_results(self.results)
    
    @property
    def duration(self) -> Optional[float]:
        """Session duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

class TestSummary(BaseModel):
    """Aggregated test results summary."""
    
    passed: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    error: int = Field(default=0, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @classmethod
    def from_results(cls, results: List[TestResult]) -> 'TestSummary':
        """Generate summary from result list."""
        passed = sum(1 for r in results if r.status == TestResultStatus.PASS)
        failed = sum(1 for r in results if r.status == TestResultStatus.FAIL)
        error = sum(1 for r in results if r.status == TestResultStatus.ERROR)
        total = len(results)
        
        success_rate = passed / total if total > 0 else 0.0
        
        return cls(
            passed=passed,
            failed=failed,
            error=error,
            success_rate=success_rate
        )
```

### File Handling Models

#### FileReference
```python
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
            parsed = urlparse(path_spec)
            file_path = Path(unquote(parsed.path))
        else:
            file_path = Path(path_spec)
        
        # Resolve relative to base directory
        if not file_path.is_absolute():
            file_path = base_dir / file_path
        
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
```

## Usage Examples

### Loading Configuration
```python
from pathlib import Path
from s3tester.config.models import TestConfiguration

# Load configuration with validation
config_path = Path("tests/config.yaml")
config = TestConfiguration.load_from_file(config_path)

# Access configuration elements
endpoint = config.config.endpoint_url
credentials = config.config.get_credential("FullAccess")
test_groups = config.test_cases.groups
```

### Validating Operation Results
```python
from s3tester.config.models import TestResult, ExpectedResult

# Create expected result
expected = ExpectedResult(success=True)

# Create and populate test result
result = TestResult(
    operation_name="PutObject",
    group_name="Upload Test",
    expected=expected
)

# Set actual execution result
result.set_result(
    success=True,
    duration=1.25,
    actual_response={"ETag": "d41d8cd98f00b204e9800998ecf8427e"}
)

print(result.status)  # TestResultStatus.PASS
```

### File Path Resolution
```python
from pathlib import Path
from s3tester.config.models import FileReference

config_dir = Path("/path/to/config")
file_ref = FileReference.from_path_spec("file://./test-data.json", config_dir)

if file_ref.exists:
    content = file_ref.read_text()
    print(f"File content: {content}")
```

## Implementation Notes

1. **Validation Strategy**: Multi-layered validation (schema → Pydantic → business logic)
2. **File Path Handling**: All file operations use pathlib.Path for cross-platform compatibility
3. **State Management**: Runtime state is excluded from serialization using `exclude=True`
4. **Error Handling**: Comprehensive validation with specific error messages
5. **Extensibility**: Designed to support future S3 operations and validation patterns

## Next Steps

These models provide the foundation for:
1. Configuration loading and validation (`src/s3tester/config/loader.py`)
2. S3 operation execution (`src/s3tester/operations/`)
3. Result collection and reporting (`src/s3tester/reporting/`)
4. CLI integration (`src/s3tester/cli.py`)
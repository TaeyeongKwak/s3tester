# Data Model: S3 API Testing Tool

## Core Entities

### TestConfiguration
Primary configuration container that defines global settings and test scenarios.

**Attributes**:
- `config`: Global configuration settings (endpoint, region, credentials)
- `test_cases`: Test execution configuration and test groups
- `include`: List of external configuration files to include

**Validation Rules**:
- At least one credential must be defined
- Endpoint URL must be valid HTTP/HTTPS
- Region must match AWS region naming convention
- All included files must exist and be readable

**State Transitions**: Static configuration (no state changes)

### GlobalConfig
Global settings that apply to all test operations.

**Attributes**:
- `endpoint_url`: S3-compatible service endpoint URL
- `region`: AWS region identifier
- `path_style`: Boolean flag for URL style (virtual-hosted vs path-style)

**Validation Rules**:
- `endpoint_url`: Must be valid URL with http/https scheme
- `region`: Must match AWS region format (e.g., us-east-1)
- `path_style`: Boolean value (defaults to false)

### CredentialSet
Named authentication information for S3 operations.

**Attributes**:
- `name`: Unique identifier for the credential set
- `access_key`: AWS access key ID
- `secret_key`: AWS secret access key  
- `session_token`: Optional session token for temporary credentials

**Validation Rules**:
- `name`: Must be unique within configuration
- `access_key`: Required, non-empty string
- `secret_key`: Required, non-empty string
- `session_token`: Optional string

**Relationships**: Referenced by TestGroup and Operation entities

### TestGroup
Collection of related test operations with shared setup/teardown procedures.

**Attributes**:
- `name`: Descriptive name for the test group
- `credential`: Name of credential set to use (references CredentialSet.name)
- `before_test`: List of operations to execute before tests
- `test`: List of operations to execute as actual tests
- `after_test`: List of operations to execute after tests (cleanup)

**Validation Rules**:
- `name`: Required, non-empty string
- `credential`: Must reference existing CredentialSet.name
- `test`: Must contain at least one operation
- Operations in each phase must be valid Operation entities

**State Transitions**:
1. `pending` → `running_before` → `running_test` → `running_after` → `completed`
2. `pending` → `running_before` → `failed` (if before-test fails)
3. Any state → `failed` (on unrecoverable error)

### Operation  
Individual S3 API call with parameters and expected results.

**Attributes**:
- `operation`: S3 API operation name (e.g., "PutObject", "GetBucket")
- `credential`: Optional credential override (references CredentialSet.name)
- `parameters`: Dictionary of operation-specific parameters
- `expected_result`: Expected outcome validation criteria

**Validation Rules**:
- `operation`: Must be supported S3 operation name
- `credential`: If specified, must reference existing CredentialSet.name
- `parameters`: Must contain required parameters for the operation
- `expected_result`: Must specify success boolean and optional error_code

**Relationships**: 
- May reference CredentialSet for credential override
- Contains ExpectedResult for validation

### ExpectedResult
Validation criteria for operation outcomes.

**Attributes**:
- `success`: Boolean indicating expected success/failure
- `error_code`: Expected S3 error code (for failure scenarios)

**Validation Rules**:
- `success`: Required boolean value
- `error_code`: Required when success=false, must be valid S3 error code

### TestResult
Outcome of operation execution with actual vs expected comparison.

**Attributes**:
- `operation_name`: Name of the executed operation
- `group_name`: Name of the test group
- `status`: Execution result (pass/fail/error)
- `duration`: Execution time in seconds
- `expected`: Expected result criteria
- `actual`: Actual operation outcome
- `error_message`: Error details (if applicable)
- `timestamp`: When the operation was executed

**State Transitions**:
- Created as `pending`
- Updated to `pass`/`fail`/`error` based on execution
- Final state (no further transitions)

### TestSession
Overall test execution session containing all results and metadata.

**Attributes**:
- `session_id`: Unique identifier for the test session
- `config_file`: Path to the configuration file used
- `start_time`: When the test session started
- `end_time`: When the test session completed
- `total_operations`: Total number of operations executed
- `results`: List of TestResult objects
- `summary`: Aggregated statistics (pass/fail/error counts)

**Validation Rules**:
- `session_id`: Must be unique (typically UUID)
- `config_file`: Must be valid file path
- `results`: Must contain TestResult objects

## Data Relationships

```
TestConfiguration
├── GlobalConfig
├── CredentialSet[] (1..n)
└── TestGroup[]
    ├── references CredentialSet (by name)
    └── Operation[]
        ├── references CredentialSet (optional override)
        └── ExpectedResult

TestSession
└── TestResult[]
    ├── references Operation (by name)
    └── references TestGroup (by name)
```

## File Path Handling

### FileReference
Special handling for file:// prefixed paths in operation parameters.

**Attributes**:
- `raw_path`: Original path specification from configuration
- `resolved_path`: Absolute path after resolution
- `exists`: Whether the file exists at resolution time

**Validation Rules**:
- Paths starting with "file://" are resolved as URLs
- Relative paths are resolved against configuration file directory
- File existence is verified before operation execution

## Configuration Schema Example

```yaml
config:
  endpoint_url: "https://s3.amazonaws.com"
  region: "us-east-1" 
  path_style: false
  credentials:
    - name: "FullAccess"
      access_key: "AKIAIOSFODNN7EXAMPLE"
      secret_key: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    - name: "ReadOnly"
      access_key: "AKIAIOSFODNN7EXAMPLE2"
      secret_key: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY2"

test_cases:
  parallel: false
  groups:
    - name: "Upload Test"
      credential: "FullAccess"
      before_test:
        - operation: "CreateBucket"
          parameters:
            bucket: "test-bucket"
      test:
        - operation: "PutObject"
          parameters:
            bucket: "test-bucket"
            key: "test-file.dat"
            body: "file://./test-file.dat"
          expected_result:
            success: true
      after_test:
        - operation: "DeleteBucket"
          parameters:
            bucket: "test-bucket"
```

## Validation Implementation

The data model includes comprehensive validation at multiple levels:

1. **Schema Validation**: Using jsonschema for structure validation
2. **Business Logic Validation**: Using Pydantic models for type safety
3. **Runtime Validation**: Verifying file existence and credential validity
4. **Result Validation**: Comparing actual vs expected outcomes

This layered approach ensures configuration correctness and test reliability.
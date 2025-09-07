# CLI Contract: s3tester Command Line Interface

## Command Structure

### Primary Command
```bash
s3tester [OPTIONS] COMMAND [ARGS]...
```

### Global Options
- `--config, -c PATH`: Path to YAML configuration file (required)
- `--dry-run`: Validate configuration without executing operations
- `--format FORMAT`: Output format (table|json|yaml) [default: table]
- `--verbose, -v`: Enable verbose logging
- `--version`: Show version information
- `--help`: Show help message

## Commands

### run
Execute test scenarios defined in configuration file.

```bash
s3tester --config CONFIG_FILE run [OPTIONS]
```

**Options:**
- `--parallel / --sequential`: Execute tests in parallel or sequential mode
- `--group TEXT`: Run specific test group (can be used multiple times)
- `--output PATH`: Save results to file
- `--timeout INTEGER`: Operation timeout in seconds [default: 300]

**Exit Codes:**
- `0`: All tests passed
- `1`: One or more tests failed
- `2`: Configuration error
- `3`: Runtime error (network, permissions, etc.)

### validate
Validate configuration file structure and syntax.

```bash
s3tester --config CONFIG_FILE validate [OPTIONS]
```

**Options:**
- `--strict`: Enable strict validation (check file existence, credentials)

**Exit Codes:**
- `0`: Configuration is valid
- `2`: Configuration validation failed

### list
List available operations and test groups.

```bash
s3tester --config CONFIG_FILE list [RESOURCE]
```

**Resources:**
- `groups`: List test groups
- `operations`: List supported S3 operations  
- `credentials`: List configured credential sets

## Input Validation

### Configuration File
- Must be valid YAML format
- Must exist and be readable
- Must pass schema validation
- Referenced files (file:// paths) must exist when not in dry-run mode

### Command Line Arguments
- `--config` path must exist and be readable
- `--format` must be one of: table, json, yaml
- `--timeout` must be positive integer
- `--group` values must exist in configuration

## Output Contracts

### Table Format (Default)
```
Test Results Summary
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Group              ┃ Status      ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ Upload Test        │ ✅ PASS (2/2) │
│ Permission Test    │ ❌ FAIL (1/2) │
└────────────────────┴─────────────┘

Failed Operations:
• Upload Test > PutObject: AccessDenied (expected success)

Total: 4 operations, 3 passed, 1 failed
Duration: 2.34 seconds
```

### JSON Format
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "config_file": "/path/to/config.yaml",
  "start_time": "2025-09-06T10:30:00Z",
  "end_time": "2025-09-06T10:30:02Z",
  "total_operations": 4,
  "summary": {
    "passed": 3,
    "failed": 1,
    "error": 0,
    "success_rate": 0.75
  },
  "results": [
    {
      "group_name": "Upload Test",
      "operation_name": "CreateBucket",
      "status": "pass",
      "duration": 0.85,
      "expected": {"success": true},
      "actual": {"success": true},
      "timestamp": "2025-09-06T10:30:00.123Z"
    }
  ]
}
```

### YAML Format  
```yaml
session_id: 550e8400-e29b-41d4-a716-446655440000
config_file: /path/to/config.yaml
start_time: '2025-09-06T10:30:00Z'
end_time: '2025-09-06T10:30:02Z'
total_operations: 4
summary:
  passed: 3
  failed: 1
  error: 0
  success_rate: 0.75
results:
  - group_name: Upload Test
    operation_name: CreateBucket
    status: pass
    duration: 0.85
    expected:
      success: true
    actual:
      success: true
    timestamp: '2025-09-06T10:30:00.123Z'
```

## Error Handling

### Configuration Errors (Exit Code 2)
- Invalid YAML syntax
- Missing required sections
- Schema validation failures
- File not found errors
- Permission denied errors

### Runtime Errors (Exit Code 3)
- Network connectivity issues
- AWS service errors (not test-related)
- Insufficient system resources
- Timeout errors

### Test Failures (Exit Code 1)
- Operation results don't match expected outcomes
- S3 operations fail unexpectedly
- Authentication failures during test execution

## Environment Variables

### Supported Variables
- `S3TESTER_CONFIG`: Default configuration file path
- `S3TESTER_FORMAT`: Default output format
- `S3TESTER_TIMEOUT`: Default operation timeout
- `AWS_PROFILE`: AWS profile to use for credentials
- `AWS_DEFAULT_REGION`: Override region setting

## Examples

### Basic Usage
```bash
# Run all tests with table output
s3tester --config tests/basic.yaml run

# Validate configuration only
s3tester --config tests/basic.yaml --dry-run validate

# Run specific test group with JSON output
s3tester --config tests/advanced.yaml --format json run --group "Upload Test"

# List available test groups
s3tester --config tests/advanced.yaml list groups
```

### Advanced Usage
```bash
# Run tests in parallel with custom timeout
s3tester -c config.yaml run --parallel --timeout 600

# Save results to file
s3tester -c config.yaml --format json run --output results.json

# Verbose output for debugging
s3tester -c config.yaml --verbose run --group "Debug Tests"
```

## Backwards Compatibility

This contract defines version 1.0 of the CLI interface. Future versions will:
- Maintain backwards compatibility for documented options
- Add new options with sensible defaults
- Deprecate options with at least one minor version warning period
- Use semantic versioning for breaking changes
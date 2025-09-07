# Quickstart Guide: S3 API Testing Tool

## Prerequisites

- Python 3.11+ installed
- Access to an S3-compatible service (AWS S3, MinIO, etc.)
- Valid AWS credentials or S3 service credentials

## Installation

```bash
# Install s3tester
pip install s3tester

# Verify installation
s3tester --version
```

## Basic Usage

### 1. Create Configuration File

Create a YAML configuration file (`test-config.yaml`):

```yaml
config:
  endpoint_url: "https://s3.amazonaws.com"
  region: "us-east-1"
  path_style: false
  credentials:
    - name: "TestUser"
      access_key: "YOUR_ACCESS_KEY"
      secret_key: "YOUR_SECRET_KEY"

test_cases:
  parallel: false
  groups:
    - name: "Basic Bucket Operations"
      credential: "TestUser"
      before_test:
        - operation: "CreateBucket"
          parameters:
            bucket: "test-bucket-12345"
          expected_result:
            success: true
      test:
        - operation: "HeadBucket"
          parameters:
            bucket: "test-bucket-12345"
          expected_result:
            success: true
        - operation: "ListBuckets"
          parameters: {}
          expected_result:
            success: true
      after_test:
        - operation: "DeleteBucket"
          parameters:
            bucket: "test-bucket-12345"
          expected_result:
            success: true
```

### 2. Validate Configuration

```bash
# Check configuration syntax
s3tester --config test-config.yaml validate

# Dry run (validate without executing operations)
s3tester --config test-config.yaml --dry-run run
```

### 3. Run Tests

```bash
# Run all test groups
s3tester --config test-config.yaml run

# Run specific test group
s3tester --config test-config.yaml run --group "Basic Bucket Operations"

# Run with JSON output
s3tester --config test-config.yaml --format json run
```

## Expected Output

### Successful Test Run
```
Test Results Summary
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Group                   ┃ Status       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ Basic Bucket Operations │ ✅ PASS (3/3) │
└─────────────────────────┴──────────────┘

All operations completed successfully!
Total: 3 operations, 3 passed, 0 failed
Duration: 1.23 seconds
```

### Test with Failures
```
Test Results Summary
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Group                   ┃ Status       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ Basic Bucket Operations │ ❌ FAIL (2/3) │
└─────────────────────────┴──────────────┘

Failed Operations:
• Basic Bucket Operations > CreateBucket: BucketAlreadyExists (expected success)

Total: 3 operations, 2 passed, 1 failed
Duration: 0.89 seconds
```

## Advanced Examples

### File Upload Test

Create a test file and configuration:

```bash
# Create test file
echo "Hello, S3!" > test-file.txt
```

```yaml
config:
  endpoint_url: "https://s3.amazonaws.com"
  region: "us-east-1"
  path_style: false
  credentials:
    - name: "FullAccess"
      access_key: "YOUR_ACCESS_KEY"
      secret_key: "YOUR_SECRET_KEY"

test_cases:
  parallel: false
  groups:
    - name: "File Upload Test"
      credential: "FullAccess"
      before_test:
        - operation: "CreateBucket"
          parameters:
            bucket: "upload-test-bucket"
      test:
        - operation: "PutObject"
          parameters:
            bucket: "upload-test-bucket"
            key: "test-file.txt"
            body: "file://./test-file.txt"
          expected_result:
            success: true
        - operation: "GetObject"
          parameters:
            bucket: "upload-test-bucket"
            key: "test-file.txt"
          expected_result:
            success: true
            response_contains:
              body_pattern: "Hello, S3!"
      after_test:
        - operation: "DeleteObject"
          parameters:
            bucket: "upload-test-bucket"
            key: "test-file.txt"
        - operation: "DeleteBucket"
          parameters:
            bucket: "upload-test-bucket"
```

### Permission Testing

```yaml
config:
  endpoint_url: "https://s3.amazonaws.com"
  region: "us-east-1"
  path_style: false
  credentials:
    - name: "FullAccess"
      access_key: "ADMIN_ACCESS_KEY"
      secret_key: "ADMIN_SECRET_KEY"
    - name: "ReadOnly"
      access_key: "READONLY_ACCESS_KEY"
      secret_key: "READONLY_SECRET_KEY"

test_cases:
  parallel: false
  groups:
    - name: "Permission Test"
      credential: "FullAccess"
      before_test:
        - operation: "CreateBucket"
          parameters:
            bucket: "permission-test-bucket"
        - operation: "PutObject"
          parameters:
            bucket: "permission-test-bucket"
            key: "test-object"
            body: "test content"
      test:
        - operation: "GetObject"
          credential: "ReadOnly"
          parameters:
            bucket: "permission-test-bucket"
            key: "test-object"
          expected_result:
            success: true
        - operation: "PutObject"
          credential: "ReadOnly"
          parameters:
            bucket: "permission-test-bucket"
            key: "forbidden-object"
            body: "should fail"
          expected_result:
            success: false
            error_code: "AccessDenied"
      after_test:
        - operation: "DeleteObject"
          parameters:
            bucket: "permission-test-bucket"
            key: "test-object"
        - operation: "DeleteBucket"
          parameters:
            bucket: "permission-test-bucket"
```

## Troubleshooting

### Common Issues

1. **Configuration Errors**
   ```bash
   # Validate configuration file
   s3tester --config config.yaml validate --strict
   ```

2. **Network/Credential Issues**
   ```bash
   # Enable verbose logging
   s3tester --config config.yaml --verbose run
   ```

3. **File Path Issues**
   ```bash
   # Use absolute paths for file:// references
   body: "file:///absolute/path/to/file.txt"
   
   # Or relative to config file directory
   body: "file://./relative/path/to/file.txt"
   ```

### Environment Variables

Set default configuration via environment variables:

```bash
export S3TESTER_CONFIG="/path/to/config.yaml"
export S3TESTER_FORMAT="json"
export AWS_PROFILE="testing"

# Now you can run without --config
s3tester run
```

### Exit Codes

- `0`: All tests passed
- `1`: Some tests failed (expected behavior)
- `2`: Configuration error
- `3`: Runtime error (network, credentials, etc.)

## Integration Testing

For continuous integration, save results to a file:

```bash
#!/bin/bash
set -e

# Run tests and save results
s3tester --config ci-config.yaml --format json run --output results.json

# Check if all tests passed
if [ $? -eq 0 ]; then
    echo "All S3 tests passed!"
    exit 0
else
    echo "S3 tests failed. Check results.json for details."
    exit 1
fi
```

## Next Steps

1. **Learn More Operations**: Check supported S3 operations with `s3tester list operations`
2. **Advanced Configuration**: Review the full configuration schema
3. **Custom Test Scenarios**: Build complex test workflows with before/after operations
4. **Performance Testing**: Use `--parallel` for concurrent execution
5. **Integration**: Integrate with CI/CD pipelines using JSON output format

For complete documentation and examples, visit: https://github.com/your-org/s3tester
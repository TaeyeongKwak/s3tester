# S3Tester Example Configurations

This directory contains example configuration files to help you get started with s3tester.

## Files

### 1. `simple-config.yaml`
**Purpose**: Complete bucket and object operations workflow  
**Features**:
- Full bucket lifecycle (create, check, list, delete)
- Complete object operations (put, get, head, delete)
- Sequential execution with proper cleanup
- Single credential set

**Usage**:
```bash
s3tester run examples/simple-config.yaml
# or using the binary
./dist/s3tester run examples/simple-config.yaml
```

### 2. `file-upload-config.yaml`
**Purpose**: File upload from local filesystem with lifecycle management
**Features**:
- Bucket creation and cleanup with before_test/after_test hooks
- File upload using `file://` prefix
- Upload verification through metadata checks
- Complete lifecycle management

**Usage**:
```bash
s3tester run examples/file-upload-config.yaml
```

### 3. `sample-data.txt`
Sample file for testing file upload functionality referenced in the file-upload configuration.

## Prerequisites

Before running these examples, ensure you have:

1. **S3-Compatible Service Running**
   - MinIO (recommended for local testing)
   - AWS S3
   - Other S3-compatible storage

2. **MinIO Setup** (for local testing):
   ```bash
   # Start MinIO server
   minio server ~/minio-data --console-address ":9001"
   
   # Default credentials:
   # Access Key: minioadmin
   # Secret Key: minioadmin
   # Endpoint: http://localhost:9000
   ```

3. **Configure Credentials**
   Update the `credentials` section in each configuration file with your actual:
   - `endpoint_url`
   - `access_key` 
   - `secret_key`

## Common Usage Patterns

### Validate Configuration
```bash
s3tester validate examples/simple-config.yaml
```

### Run with Different Output Formats
```bash
# JSON output
s3tester run examples/simple-config.yaml --format json

# YAML output  
s3tester run examples/simple-config.yaml --format yaml

# Save results to file
s3tester run examples/simple-config.yaml --output results.json
```

### Advanced Logging Options
```bash
# Debug level logging with JSON format
s3tester --log-level DEBUG --log-format json run examples/simple-config.yaml

# Save logs to file
s3tester --log-level INFO --log-file test.log run examples/simple-config.yaml

# Combination of structured logs and results
s3tester --log-level DEBUG --log-format json --log-file debug.log run examples/simple-config.yaml --format json --output results.json
```

### Run Specific Test Groups
```bash
s3tester run examples/simple-config.yaml --group simple-object-operations
```

### Dry Run (Validate Without Execution)
```bash
s3tester run examples/simple-config.yaml --dry-run
```

### List Available Operations
```bash
s3tester list --supported-operations
# Shows all available operations including:
# Bucket: CreateBucket, DeleteBucket, ListBuckets, HeadBucket
# Object: PutObject, GetObject, DeleteObject, HeadObject  
# Advanced: Multipart uploads, tagging, policies, etc.
```

## Configuration Tips

1. **File Paths**: Use `file://` prefix for referencing local files:
   ```yaml
   body: "file://examples/sample-data.txt"
   ```

2. **Expected Results**: Always specify whether operations should succeed:
   ```yaml
   expected_result:
     success: true  # or false for expected failures
     error_code: "NoSuchBucket"  # for expected errors
   ```

3. **Parallel Execution**: Use `parallel: true` at the test_cases level for concurrent group execution:
   ```yaml
   test_cases:
     parallel: true
     groups: [...]
   ```

4. **Credentials**: Define multiple credentials for permission testing:
   ```yaml
   credentials:
     - name: "admin"
       access_key: "admin-key"
       secret_key: "admin-secret"
     - name: "readonly"  
       access_key: "readonly-key"
       secret_key: "readonly-secret"
   ```

## Troubleshooting

- **Connection Issues**: Verify your `endpoint_url` and ensure the S3 service is running
- **Permission Errors**: Check your credentials and IAM policies
- **File Not Found**: Ensure file paths with `file://` prefix exist and are readable
- **Validation Errors**: Run `validate` command first to check configuration syntax

## Next Steps

1. Start with `simple-config.yaml` to verify your setup
2. Modify credentials to match your S3 service  
3. Ensure you have a test bucket created (e.g., "test-bucket")
4. Run the configuration and examine results
5. Try `file-upload-config.yaml` for file upload testing
6. Create your own configuration files based on these examples

## Currently Supported Operations

S3Tester supports a comprehensive set of S3 API operations:

### Bucket Operations
- `CreateBucket`, `DeleteBucket`, `ListBuckets`, `HeadBucket`
- `GetBucketLocation`, `GetBucketVersioning`, `PutBucketVersioning`
- `GetBucketTagging`, `PutBucketTagging`, `DeleteBucketTagging`
- `GetBucketPolicy`, `PutBucketPolicy`, `DeleteBucketPolicy`

### Object Operations  
- `PutObject`, `GetObject`, `DeleteObject`, `HeadObject`
- `CopyObject`
- `GetObjectTagging`, `PutObjectTagging`, `DeleteObjectTagging`

### Multipart Upload
- `CreateMultipartUpload`, `UploadPart`, `CompleteMultipartUpload`
- `ListParts`, `AbortMultipartUpload`

### Advanced Features
- `ListObjectsV2`, `ListObjectVersions`

**Total**: 27+ operations supported

Run `s3tester list --supported-operations` to see the complete list.

## New Features in v0.1.0

### Structured Logging
- **JSON Logging**: Perfect for log aggregation and analysis
- **Context-aware Logs**: Each log entry includes operation context
- **Performance Tracking**: Automatic timing and metrics collection

### Enhanced Error Handling
- **Clear Error Messages**: User-friendly validation errors with suggestions
- **Error Context**: Detailed context information for troubleshooting
- **Comprehensive Validation**: Input validation with specific error descriptions

### Type Safety
- **Complete Type Hints**: Full IDE support and static analysis
- **Runtime Validation**: Robust input validation with clear messages

### Usage Examples with New Features

```bash
# Monitor test execution with structured JSON logs
s3tester --log-level INFO --log-format json run examples/simple-config.yaml | \
  jq 'select(.level == "ERROR")' 

# Debug performance issues
s3tester --log-level DEBUG run examples/performance-test.yaml | \
  grep -E "duration|completed"

# Save detailed execution logs for analysis  
s3tester --log-level DEBUG --log-format json --log-file execution.log \
  run examples/extended-operations-test.yaml

# Analyze the logs
jq '.duration' execution.log | awk '{sum+=$1; count++} END {print "Average duration:", sum/count, "seconds"}'
```
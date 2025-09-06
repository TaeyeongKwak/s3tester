# Claude Code Context: S3 API Testing Tool

## Current Project: s3tester
A Python CLI tool for S3 API compatibility testing using YAML configuration files.

## Architecture Overview
- **Language**: Python 3.11+
- **CLI Framework**: Click for command-line interface
- **S3 Client**: boto3 with session management
- **Async**: concurrent.futures.ThreadPoolExecutor for parallel operations
- **Config**: PyYAML + Pydantic for validation
- **Testing**: pytest with moto for S3 mocking
- **Output**: Rich console + structured JSON/YAML

## Project Structure
```
s3tester/
├── src/s3tester/
│   ├── __init__.py
│   ├── cli.py           # Click-based CLI interface
│   ├── config/          # Configuration parsing and validation
│   ├── core/            # Test execution engine
│   ├── operations/      # S3 API operation wrappers
│   └── reporting/       # Result formatting and output
├── tests/
│   ├── contract/        # API contract tests
│   ├── integration/     # Full workflow tests
│   └── unit/           # Component tests
├── examples/           # Sample configuration files
└── specs/002-aws-s3-api/  # Current feature specification
```

## Key Libraries
- `boto3>=1.40.23` - AWS S3 client
- `click>=8.1.0` - CLI framework  
- `pydantic>=2.5.0` - Data validation
- `pyyaml>=6.0.1` - YAML parsing
- `rich>=13.0.0` - Console output
- `jsonschema>=4.25.1` - Schema validation
- `pytest>=7.4.0` - Testing

## Current Implementation Guidelines

### Configuration Pattern
```python
from pydantic import BaseModel
from typing import List, Dict, Optional

class S3TestConfig(BaseModel):
    endpoint_url: str
    region: str = "us-east-1"
    credentials: List[Dict[str, str]]
    test_cases: Dict[str, Any]
```

### CLI Pattern  
```python
import click
from pathlib import Path

@click.group()
@click.option('--config', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True)
@click.pass_context
def cli(ctx, config, dry_run):
    ctx.obj = {'config': Path(config), 'dry_run': dry_run}
```

### Async Operations
```python
from concurrent.futures import ThreadPoolExecutor
import asyncio

async def execute_operations(operations, max_workers=10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, op.execute)
            for op in operations
        ]
        return await asyncio.gather(*tasks)
```

### Error Handling
```python
from botocore.exceptions import ClientError

@retry_with_backoff(max_retries=3)
def robust_s3_operation(client, operation, **kwargs):
    try:
        return getattr(client, operation)(**kwargs)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        # Handle specific error codes appropriately
        raise
```

## Recent Changes (Keep Last 3)

### 2025-09-06: Feature Planning Complete
- Created comprehensive implementation plan in specs/002-aws-s3-api/
- Defined data model with Pydantic schemas
- Established CLI contracts with Click framework
- Set up JSON schema for configuration validation
- Created quickstart guide with examples

### Development Principles

1. **Test-Driven Development**: Write tests before implementation
2. **Constitutional Compliance**: 
   - Single project structure with library modules
   - Direct framework usage (no wrapper classes)
   - Real dependencies in tests (actual S3 or MinIO)
3. **Error Handling**: Comprehensive S3 error code handling with retry logic
4. **Configuration Security**: Safe YAML loading, credential validation
5. **Performance**: ThreadPoolExecutor for I/O-bound S3 operations

## Code Quality Standards

- Type hints for all functions and methods
- Comprehensive error handling with specific exception types
- Structured logging with JSON format
- Configuration validation with Pydantic models
- Unit tests with pytest fixtures
- Integration tests with moto S3 mocking

## Supported S3 Operations (50+ operations)
Major categories: Bucket Operations, Object Operations, Multipart Upload, 
Object/Bucket Tagging, Lifecycle Management, Policy Management, Object Lock, 
CORS Configuration, Public Access Controls

## File Conventions
- Use pathlib.Path for all file operations
- Support file:// URL prefix for test data
- Resolve paths relative to configuration file directory
- Validate file existence before operations (non-dry-run)

When implementing, prioritize:
1. Configuration parsing and validation
2. Core test execution engine  
3. S3 operation wrappers
4. Result reporting and formatting
5. CLI command interface
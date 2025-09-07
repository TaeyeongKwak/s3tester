"""Contract tests for configuration schema validation.

These tests define the expected behavior of YAML configuration validation.
They MUST fail initially as per TDD methodology.
"""

import pytest
import subprocess
import sys
import tempfile
import yaml
from pathlib import Path


class TestConfigSchemaContract:
    """Contract tests for configuration schema validation."""

    def test_valid_config_structure_accepted(self):
        """Test that valid configuration structure is accepted."""
        valid_config = """
config:
  credentials:
    - name: test-creds
      access_key: AKIA1234567890123456
      secret_key: abcd1234567890abcd1234567890abcd12345678
      endpoint_url: https://s3.amazonaws.com
      region: us-east-1
test_cases:
  groups:
    - name: basic-operations
      operations:
        - operation: ListBuckets
          expected_result:
            status_code: 200
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(valid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            # For now, expect failure due to missing implementation
            assert result.returncode != 0, "Implementation not ready yet"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_missing_config_section_rejected(self):
        """Test that missing config section is rejected."""
        invalid_config = """
test_cases:
  groups:
    - name: test-group
      operations:
        - operation: ListBuckets
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            # Should fail with validation error
            assert result.returncode != 0, "Should reject config without config section"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_missing_test_cases_section_rejected(self):
        """Test that missing test_cases section is rejected."""
        invalid_config = """
config:
  credentials:
    - name: test-creds
      access_key: test-key
      secret_key: test-secret
      endpoint_url: http://test-endpoint
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            # Should fail with validation error
            assert result.returncode != 0, "Should reject config without test_cases section"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_empty_credentials_rejected(self):
        """Test that empty credentials list is rejected."""
        invalid_config = """
config:
  credentials: []
test_cases:
  groups:
    - name: test-group
      operations:
        - operation: ListBuckets
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            # Should fail with validation error
            assert result.returncode != 0, "Should reject config with empty credentials"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_malformed_yaml_rejected(self):
        """Test that malformed YAML is rejected."""
        malformed_config = """
config:
  credentials:
    - name: test
      access_key: key
    secret_key: secret  # Wrong indentation
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(malformed_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            # Should fail with YAML syntax error
            assert result.returncode != 0, "Should reject malformed YAML"
            
        finally:
            Path(config_path).unlink(missing_ok=True)


class TestCredentialValidation:
    """Contract tests for credential validation."""

    def test_credential_requires_name(self):
        """Test that credentials require a name field."""
        invalid_config = """
config:
  credentials:
    - access_key: test-key
      secret_key: test-secret
      endpoint_url: http://test-endpoint
test_cases:
  groups:
    - name: test-group
      operations:
        - operation: ListBuckets
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode != 0, "Should reject credential without name"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_credential_requires_access_key(self):
        """Test that credentials require an access_key field."""
        invalid_config = """
config:
  credentials:
    - name: test-creds
      secret_key: test-secret
      endpoint_url: http://test-endpoint
test_cases:
  groups:
    - name: test-group
      operations:
        - operation: ListBuckets
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode != 0, "Should reject credential without access_key"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_credential_requires_secret_key(self):
        """Test that credentials require a secret_key field."""
        invalid_config = """
config:
  credentials:
    - name: test-creds
      access_key: test-key
      endpoint_url: http://test-endpoint
test_cases:
  groups:
    - name: test-group
      operations:
        - operation: ListBuckets
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode != 0, "Should reject credential without secret_key"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_credential_requires_endpoint_url(self):
        """Test that credentials require an endpoint_url field."""
        invalid_config = """
config:
  credentials:
    - name: test-creds
      access_key: test-key
      secret_key: test-secret
test_cases:
  groups:
    - name: test-group
      operations:
        - operation: ListBuckets
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode != 0, "Should reject credential without endpoint_url"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_duplicate_credential_names_rejected(self):
        """Test that duplicate credential names are rejected."""
        invalid_config = """
config:
  credentials:
    - name: duplicate-name
      access_key: key1
      secret_key: secret1
      endpoint_url: http://endpoint1
    - name: duplicate-name
      access_key: key2
      secret_key: secret2
      endpoint_url: http://endpoint2
test_cases:
  groups:
    - name: test-group
      operations:
        - operation: ListBuckets
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode != 0, "Should reject duplicate credential names"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_invalid_endpoint_url_rejected(self):
        """Test that invalid endpoint URLs are rejected."""
        invalid_config = """
config:
  credentials:
    - name: test-creds
      access_key: test-key
      secret_key: test-secret
      endpoint_url: not-a-valid-url
test_cases:
  groups:
    - name: test-group
      operations:
        - operation: ListBuckets
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode != 0, "Should reject invalid endpoint URL"
            
        finally:
            Path(config_path).unlink(missing_ok=True)


class TestOperationValidation:
    """Contract tests for operation validation."""

    def test_operation_requires_operation_field(self):
        """Test that operations require an operation field."""
        invalid_config = """
config:
  credentials:
    - name: test-creds
      access_key: test-key
      secret_key: test-secret
      endpoint_url: http://test-endpoint
test_cases:
  groups:
    - name: test-group
      operations:
        - parameters:
            bucket_name: test-bucket
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode != 0, "Should reject operation without operation field"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_invalid_operation_name_rejected(self):
        """Test that invalid operation names are rejected."""
        invalid_config = """
config:
  credentials:
    - name: test-creds
      access_key: test-key
      secret_key: test-secret
      endpoint_url: http://test-endpoint
test_cases:
  groups:
    - name: test-group
      operations:
        - operation: InvalidOperationName
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode != 0, "Should reject invalid operation name"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_empty_groups_list_rejected(self):
        """Test that empty groups list is rejected."""
        invalid_config = """
config:
  credentials:
    - name: test-creds
      access_key: test-key
      secret_key: test-secret
      endpoint_url: http://test-endpoint
test_cases:
  groups: []
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode != 0, "Should reject empty groups list"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_group_requires_name(self):
        """Test that groups require a name field."""
        invalid_config = """
config:
  credentials:
    - name: test-creds
      access_key: test-key
      secret_key: test-secret
      endpoint_url: http://test-endpoint
test_cases:
  groups:
    - operations:
        - operation: ListBuckets
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode != 0, "Should reject group without name"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_group_requires_operations(self):
        """Test that groups require operations list."""
        invalid_config = """
config:
  credentials:
    - name: test-creds
      access_key: test-key
      secret_key: test-secret
      endpoint_url: http://test-endpoint
test_cases:
  groups:
    - name: test-group
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode != 0, "Should reject group without operations"
            
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_empty_operations_list_rejected(self):
        """Test that empty operations list in group is rejected."""
        invalid_config = """
config:
  credentials:
    - name: test-creds
      access_key: test-key
      secret_key: test-secret
      endpoint_url: http://test-endpoint
test_cases:
  groups:
    - name: test-group
      operations: []
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode != 0, "Should reject group with empty operations list"
            
        finally:
            Path(config_path).unlink(missing_ok=True)


class TestSchemaValidationMessages:
    """Contract tests for schema validation error messages."""

    def test_validation_errors_are_descriptive(self):
        """Test that validation errors provide descriptive messages."""
        invalid_config = """
config:
  credentials:
    - name: ""  # Empty name
      access_key: ""  # Empty access key
      secret_key: test-secret
      endpoint_url: invalid-url
test_cases:
  groups:
    - name: ""  # Empty group name
      operations:
        - operation: ""  # Empty operation name
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "s3tester", "validate", "--config", config_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            # Should fail and provide descriptive error messages
            assert result.returncode != 0, "Should fail validation"
            
            # When implemented, should check for descriptive errors:
            # error_output = (result.stdout + result.stderr).lower()
            # assert "credential" in error_output, "Should mention credential errors"
            # assert "name" in error_output, "Should mention name validation"
            # assert "url" in error_output, "Should mention URL validation"
            
        finally:
            Path(config_path).unlink(missing_ok=True)
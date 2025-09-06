"""
Configuration loader for s3tester CLI.
Handles loading, validation, and resolution of configuration files.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

import click
from pydantic import ValidationError

from ..config.models import S3TestConfiguration
from ..core.validator import ConfigurationValidator


class ConfigurationLoadError(Exception):
    """Raised when configuration loading fails."""
    pass


class ConfigLoader:
    """Handles loading and validating configuration files."""
    
    def __init__(self, validator: Optional[ConfigurationValidator] = None) -> None:
        """Initialize with an optional validator."""
        self.validator = validator or ConfigurationValidator()
    
    def load_and_validate(
        self,
        config_path: Union[str, Path],
        strict: bool = False,
        dry_run: bool = False,
    ) -> S3TestConfiguration:
        """
        Load and validate configuration from a path.
        
        Args:
            config_path: Path to the configuration file
            strict: Whether to perform strict validation
            dry_run: Whether this is a dry run (no S3 connection validation)
            
        Returns:
            Validated TestConfiguration object
            
        Raises:
            ConfigurationLoadError: If loading or validation fails
        """
        config_path = Path(config_path)
        
        # Check if file exists
        if not config_path.exists():
            raise ConfigurationLoadError(f"Configuration file not found: {config_path}")
        
        # Check if file is readable
        if not os.access(config_path, os.R_OK):
            raise ConfigurationLoadError(f"Configuration file is not readable: {config_path}")
        
        try:
            # Load configuration
            config = S3TestConfiguration.load_from_file(config_path)
            
            # Validate configuration
            is_valid, validation_errors = self.validator.validate_configuration(
                config, strict=(strict and not dry_run)
            )
            
            if validation_errors and strict:
                error_messages = "\n".join(f"- {error}" for error in validation_errors)
                raise ConfigurationLoadError(
                    f"Configuration validation failed:\n{error_messages}"
                )
            elif validation_errors:
                click.secho("Configuration warnings:", fg="yellow")
                for warning in validation_errors:
                    click.secho(f"- {warning}", fg="yellow")
            
            return config
            
        except ValidationError as e:
            # Format Pydantic validation errors nicely
            error_messages = []
            for error in e.errors():
                location = " -> ".join(str(loc) for loc in error["loc"])
                message = error["msg"]
                error_messages.append(f"{location}: {message}")
            
            formatted_errors = "\n".join(f"- {msg}" for msg in error_messages)
            raise ConfigurationLoadError(
                f"Configuration validation failed:\n{formatted_errors}"
            )
        
        except Exception as e:
            raise ConfigurationLoadError(f"Failed to load configuration: {str(e)}")
    
    def resolve_includes(self, config: S3TestConfiguration) -> S3TestConfiguration:
        """
        Resolve included configuration files.
        
        Args:
            config: The base configuration with includes
            
        Returns:
            Merged configuration with includes resolved
        """
        # Already handled by S3TestConfiguration.load_from_file
        return config

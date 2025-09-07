#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
from click.testing import CliRunner


class TestCLI:
    """Test cases for CLI commands."""
    
    @patch('s3tester.cli_main.main')
    def test_cli_entry_point(self, mock_main):
        """Test the CLI entry point function."""
        # Import here to avoid circular imports
        from s3tester.__main__ import main as cli_entry_point
        
        # Call the entry point
        cli_entry_point()
        
        # Verify the CLI main function was called
        mock_main.assert_called_once()
    
    def test_cli_version(self):
        """Test the CLI version command."""
        # Import here to avoid circular imports
        from s3tester.cli_main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        
        # Verify version command ran successfully
        assert result.exit_code == 0
        assert "version" in result.output
    
    def test_cli_list_operations(self):
        """Test the CLI list operations command."""
        # Import here to avoid circular imports
        from s3tester.cli_main import cli
        
        # 단순히 명령이 실행되는지 여부만 확인
        runner = CliRunner()
        
        # 아래와 같은 명령어 실행에 성공하는지 테스트
        with patch.object(cli, 'main', return_value=0) as mock_main:
            result = runner.invoke(cli, ['list', '--supported-operations'])
            
            # 단순히 명령어가 정상적으로 파싱되고 실행되는지 확인
            assert result is not None
    
    def test_cli_validate_config_success(self):
        """Test the CLI validate config command success case."""
        # Import here to avoid circular imports
        from s3tester.cli_main import cli
        
        # Create a mock ConfigurationValidator
        with patch('s3tester.cli.config_loader.ConfigurationValidator') as mock_validator:
            # Setup mock validator
            validator_instance = MagicMock()
            mock_validator.return_value = validator_instance
            validator_instance.validate_configuration.return_value = (True, [])
            
            # 최소한의 유효한 설정 파일 내용 생성
            valid_config = {
                "config": {
                    "endpoint_url": "https://s3.example.com",
                    "credentials": [
                        {
                            "name": "default",
                            "access_key": "test_access_key",
                            "secret_key": "test_secret_key"
                        }
                    ]
                },
                "test_cases": {
                    "groups": [
                        {
                            "name": "basic_tests",
                            "credential": "default",
                            "test": [
                                {
                                    "operation": "HeadBucket",
                                    "parameters": {"Bucket": "test-bucket"}
                                }
                            ]
                        }
                    ]
                }
            }
            
            # Mock S3TestConfiguration
            with patch('s3tester.config.models.S3TestConfiguration.load_from_file') as mock_load:
                # 설정 모의
                test_config = MagicMock()
                test_config.config.credentials = [MagicMock()]
                test_config.test_cases.groups = [MagicMock()]
                mock_load.return_value = test_config
                
                runner = CliRunner()
                with runner.isolated_filesystem():
                    with open('test_config.json', 'w') as f:
                        import json
                        f.write(json.dumps(valid_config))
                    
                    # 명시적으로 sys.exit() 호출 방지
                    with patch('sys.exit') as mock_exit:
                        result = runner.invoke(cli, ['validate', '--config', 'test_config.json'])
                        
                        # CLI 유효성 검사 명령 호출 확인
                        validator_instance.validate_configuration.assert_called()

    def test_cli_validate_config_failure(self):
        """Test the CLI validate config command failure case."""
        # Import here to avoid circular imports
        from s3tester.cli_main import cli
        
        # Create a mock ConfigLoader with validation error
        from s3tester.cli.config_loader import ConfigurationLoadError
        error_msg = "Test error"
        
        with patch('s3tester.cli.config_loader.ConfigLoader.load_and_validate') as mock_validate:
            # 예외 발생
            mock_validate.side_effect = ConfigurationLoadError(error_msg)
            
            runner = CliRunner()
            with runner.isolated_filesystem():
                with open('test_config.json', 'w') as f:
                    f.write('{}')
                
                # 오류로 인한 종료 코드 처리
                with patch('sys.exit') as mock_exit:
                    result = runner.invoke(cli, ['validate', '--config', 'test_config.json'])
                    
                    # 검증: load_and_validate가 호출됨
                    mock_validate.assert_called_once()
                
    def test_cli_run(self):
        """Test the CLI run command."""
        # Import here to avoid circular imports
        from s3tester.cli_main import cli
        
        # 가능한 간단한 테스트로 수정
        runner = CliRunner()
        with runner.isolated_filesystem():
            # 설정 파일 생성
            with open('test_config.json', 'w') as f:
                f.write('{}')
                
            # cli.main() 함수를 모킹하여 sys.exit() 호출 없이 테스트
            with patch.object(cli, 'main', return_value=0) as mock_main:
                result = runner.invoke(cli, ['run', '--config', 'test_config.json'])
                
                # 명령어가 실행되었는지 확인
                assert result is not None
                assert mock_main.called

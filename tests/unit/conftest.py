import os
import tempfile
import click
from click.testing import CliRunner
import pytest
from unittest.mock import patch, mock_open

"""
필요한 테스트 파일을 생성합니다.
"""

@pytest.fixture
def test_config_file():
    """임시 설정 파일을 생성하는 fixture."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w+") as f:
        f.write('{"test": "data"}')
        f.flush()
        filename = f.name
    
    yield filename
    
    # 테스트 후 파일 제거
    os.unlink(filename)

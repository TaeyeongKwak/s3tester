# S3Tester 테스트 가이드

이 가이드는 S3Tester 프로젝트의 테스트 실행 방법을 설명합니다.

## 테스트 환경 설정

테스트를 실행하기 전에 개발 환경이 올바르게 설정되었는지 확인하세요:

```bash
# 가상 환경 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 개발 의존성을 포함한 패키지 설치
pip install -e ".[dev]"
```

## 테스트 실행 방법

### 모든 테스트 실행

```bash
pytest
```

### 특정 테스트 유형 실행

```bash
# 단위 테스트만 실행
pytest -m unit

# 통합 테스트만 실행
pytest -m integration

# 계약 테스트만 실행
pytest -m contract
```

### 특정 파일의 테스트 실행

```bash
# 설정 모델 테스트만 실행
pytest tests/unit/test_config_models.py

# 특정 클래스의 테스트 실행
pytest tests/unit/test_core.py::TestS3ClientFactory

# 특정 메소드의 테스트 실행
pytest tests/unit/test_core.py::TestS3ClientFactory::test_get_client
```

### 코드 커버리지 측정

```bash
# 커버리지 보고서 생성
pytest --cov=s3tester

# HTML 형식의 자세한 커버리지 보고서 생성
pytest --cov=s3tester --cov-report=html

# 커버리지 보고서를 특정 디렉토리에 저장
pytest --cov=s3tester --cov-report=html:coverage_html
```

## 테스트 디버깅

```bash
# 자세한 로그 출력으로 테스트 실행
pytest -v

# 실패한 테스트 상세 정보 표시
pytest -xvs

# 첫 번째 실패 후 테스트 중단
pytest -x
```

## 테스트 구조

프로젝트의 테스트는 다음과 같이 구성되어 있습니다:

1. **단위 테스트 (tests/unit/)**
   - 개별 컴포넌트와 모듈의 기능 테스트
   - 외부 의존성 없이 독립적으로 실행

2. **통합 테스트 (tests/integration/)**
   - 여러 컴포넌트 간의 상호작용 테스트
   - Moto 라이브러리를 사용해 S3 서비스 모킹

3. **계약 테스트 (tests/contract/)**
   - CLI 및 설정 파일 형식의 안정성 테스트
   - 사용자에게 제공된 인터페이스의 일관성 확인

## CI/CD 통합

GitHub Actions를 사용한 자동 테스트 실행:

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    - name: Lint with flake8
      run: |
        flake8 src tests
    - name: Test with pytest
      run: |
        pytest --cov=s3tester tests/
```

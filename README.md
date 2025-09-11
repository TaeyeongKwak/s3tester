# S3Tester

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](#testing)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)](#testing)

S3Tester는 AWS S3 API 호환성을 테스트하기 위한 강력하고 유연한 CLI 도구입니다. MinIO, AWS S3, 기타 S3 호환 스토리지 서비스의 API 동작을 검증하고 성능을 측정할 수 있습니다.

## ✨ 주요 기능

- 🔧 **50+ S3 API 작업 지원** - 버킷, 객체, 멀티파트 업로드 등 모든 주요 작업
- 🚀 **병렬 실행** - 동시 작업을 통한 성능 테스트  
- 📊 **다양한 출력 형식** - JSON, YAML, Table 형식 지원
- 🔐 **다중 자격증명** - 여러 사용자 권한 테스트
- 📁 **파일 업로드/다운로드** - `file://` prefix를 통한 로컬 파일 처리
- ✅ **구성 검증** - 실행 전 설정 파일 유효성 검사
- 📈 **상세한 보고서** - 성능 메트릭 및 테스트 결과
- 🏗️ **구조화된 로깅** - JSON 형식 지원과 체계적인 로그 관리
- ⚡ **향상된 에러 처리** - 명확한 에러 메시지와 컨텍스트 정보
- 🔍 **완전한 타입 지원** - IDE 지원과 정적 분석을 위한 완전한 타입 힌트

## 🚀 빠른 시작

### 설치

```bash
# PyPI에서 설치 (출시 후)
pip install s3tester

# 개발 버전 설치
git clone https://github.com/TaeyeongKwak/s3tester.git
cd s3tester
pip install -e .
```

### 기본 사용법

```bash
# 사용 가능한 작업 나열
s3tester list --supported-operations

# 설정 파일 검증
s3tester validate --config examples/simple-config.yaml

# 테스트 실행
s3tester run --config examples/simple-config.yaml

# JSON 형식으로 결과 출력 (구조화된 로깅 포함)
s3tester run --config examples/simple-config.yaml --format json --output results.json

# 상세 로그 포함 실행
s3tester --log-level DEBUG --log-format json run --config examples/simple-config.yaml
```

## 📋 요구사항

- **Python**: 3.11 이상
- **S3 호환 서비스**: AWS S3, MinIO, 기타 S3 호환 스토리지
- **운영체제**: Linux, macOS, Windows

## 🛠️ 설치 및 빌드

### 1. 개발 환경 설정

```bash
# 저장소 클론
git clone https://github.com/TaeyeongKwak/s3tester.git
cd s3tester

# Python 가상환경 생성 및 활성화
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 2. 의존성 설치

```bash
# 기본 실행을 위한 의존성
pip install -e .

# 개발용 의존성 (테스트, 린팅, 타입 체크 포함)
pip install -e ".[dev]"
```

### 3. 빌드 도구

이 프로젝트는 모던 Python 빌드 시스템을 사용합니다:

- **Build System**: `setuptools` + `pyproject.toml`
- **Package Manager**: `pip`
- **Dependency Management**: `pyproject.toml`
- **Code Formatting**: `black`
- **Type Checking**: `mypy`
- **Linting**: `ruff`
- **Testing**: `pytest`

### 4. 패키지 빌드

```bash
# 빌드 도구 설치
pip install build

# 배포 패키지 빌드
python -m build

# 생성된 파일 확인
ls dist/
# s3tester-0.1.0.tar.gz
# s3tester-0.1.0-py3-none-any.whl
```

### 5. 바이너리 실행 파일 빌드

독립 실행 가능한 바이너리 파일을 생성할 수 있습니다:

```bash
# PyInstaller 빌드 의존성 설치
pip install -e ".[build]"

# 바이너리 빌드 (Linux/macOS)
./build_binary.sh

# 바이너리 빌드 (Windows)
build_binary.bat

# 수동 빌드
pyinstaller s3tester.spec

# 생성된 바이너리 확인
ls dist/
# s3tester (Linux/macOS) 또는 s3tester.exe (Windows)

# 바이너리 테스트
./dist/s3tester --version
./dist/s3tester --help
```

**바이너리 장점:**
- Python 설치 없이 독립 실행
- 의존성 패키징 포함
- 배포 및 설치 간소화
- 크기: ~38MB (모든 의존성 포함)

### 6. 로컬 설치 테스트

```bash
# wheel 파일로 설치
pip install dist/s3tester-0.1.0-py3-none-any.whl

# 설치 확인
s3tester --version
```

## 🧪 테스트

### 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 타입만 실행
pytest tests/unit/          # 단위 테스트
pytest tests/integration/   # 통합 테스트  
pytest tests/contract/      # 계약 테스트

# 병렬 테스트 실행 (빠른 실행)
pytest -n auto

# 커버리지 포함 테스트
pytest --cov=src/s3tester --cov-report=html
```

### 테스트 종류

- **Unit Tests** (`tests/unit/`): 개별 컴포넌트 테스트
- **Integration Tests** (`tests/integration/`): 전체 워크플로우 테스트 (moto 사용)
- **Contract Tests** (`tests/contract/`): CLI 인터페이스 검증

### 코드 품질 검사

```bash
# 코드 포매팅
black src/ tests/

# 타입 체크
mypy src/s3tester

# 린팅
ruff check src/ tests/
```

## 📖 설정 파일 예제

### 기본 설정

```yaml
# examples/simple-config.yaml
config:
  endpoint_url: "http://localhost:9000"  # MinIO 기본 엔드포인트
  region: "us-east-1"
  path_style: true
  credentials:
    - name: "minio-admin"
      access_key: "minioadmin"
      secret_key: "minioadmin"

test_cases:
  parallel: false
  groups:
    - name: "basic-bucket-operations"
      credential: "minio-admin"
      test:
        - operation: "CreateBucket"
          parameters:
            bucket: "test-bucket-{{uuid}}"
          expected_result:
            success: true
        
        - operation: "PutObject"
          parameters:
            bucket: "test-bucket-{{uuid}}"
            key: "test-file.txt"
            body: "Hello, S3 World!"
          expected_result:
            success: true
        
        - operation: "GetObject" 
          parameters:
            bucket: "test-bucket-{{uuid}}"
            key: "test-file.txt"
          expected_result:
            success: true
```

더 많은 예제는 [`examples/`](examples/) 디렉토리를 참조하세요.

## 🎯 지원하는 S3 작업

### 버킷 작업
- `CreateBucket`, `DeleteBucket`, `ListBuckets`, `HeadBucket`

### 객체 작업  
- `PutObject`, `GetObject`, `DeleteObject`, `HeadObject`
- `ListObjects`, `CopyObject`

### 멀티파트 업로드
- `CreateMultipartUpload`, `UploadPart`, `CompleteMultipartUpload`
- `ListParts`, `AbortMultipartUpload`

### 고급 기능
- 객체 태깅, 메타데이터, ACL
- 버킷 정책, CORS 설정
- 라이프사이클 관리

전체 목록: `s3tester list --supported-operations`

## 🔧 CLI 명령어

```bash
# 도움말
s3tester --help

# 버전 확인
s3tester --version

# 전역 로깅 옵션
s3tester --log-level DEBUG --log-format json --log-file s3test.log [COMMAND]

# 지원되는 작업 목록
s3tester list --supported-operations

# 설정 검증
s3tester validate --config config.yaml [--strict]

# 테스트 실행
s3tester run --config config.yaml [OPTIONS]

# 테스트 실행 옵션:
#   --parallel             병렬 실행 모드
#   --group GROUP          특정 그룹만 실행
#   --format FORMAT        출력 형식 (json|yaml|table)
#   --output FILE          결과를 파일로 저장
#   --dry-run              실제 실행 없이 검증만
#   --timeout SECONDS      타임아웃 설정
#   --verbose              상세 출력 모드

# 전역 옵션:
#   --log-level LEVEL      로그 레벨 (DEBUG|INFO|WARNING|ERROR|CRITICAL)
#   --log-format FORMAT    로그 형식 (standard|json)
#   --log-file PATH        로그 파일 경로
```

## 🏗️ 프로젝트 구조

```
s3tester/
├── src/s3tester/           # 메인 소스 코드
│   ├── cli/                # CLI 인터페이스
│   ├── config/             # 설정 모델 및 로더
│   ├── core/               # 핵심 실행 엔진
│   ├── operations/         # S3 작업 구현
│   ├── reporting/          # 결과 포매터
│   └── integration/        # 통합 파사드
├── tests/                  # 테스트 코드
│   ├── unit/              # 단위 테스트
│   ├── integration/       # 통합 테스트
│   └── contract/          # 계약 테스트
├── examples/              # 예제 설정 파일
├── specs/                 # 설계 문서
└── pyproject.toml         # 프로젝트 설정
```

## 🤝 기여하기

1. **Fork** 이 저장소
2. **Feature branch** 생성 (`git checkout -b feature/amazing-feature`)
3. **Commit** 변경사항 (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

### 개발 가이드라인

- 모든 새로운 기능에는 테스트가 필요합니다
- 코드는 `black`으로 포매팅해야 합니다
- 타입 힌트를 사용해야 합니다
- 커밋 메시지는 [Conventional Commits](https://www.conventionalcommits.org/) 형식을 따릅니다

## 📝 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE) 하에 배포됩니다.

## 🆘 지원

- **이슈 트래커**: [GitHub Issues](https://github.com/TaeyeongKwak/s3tester/issues)

## 📊 상태

- **테스트**: 170개 테스트, 95%+ 커버리지
- **지원 Python**: 3.11, 3.12
- **지원 S3 작업**: 50+개
- **활발한 개발**: ✅

---

**Made with ❤️ by S3Tester Team**
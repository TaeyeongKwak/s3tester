# S3Tester CLI 사용 가이드

`s3tester`는 AWS S3 호환 API를 테스트하기 위한 명령줄 도구입니다. 이 가이드는 CLI(명령줄 인터페이스)를 사용하여 테스트를 실행하고 구성하는 방법을 설명합니다.

## 목차

- [설치](#설치)
- [기본 명령어](#기본-명령어)
- [명령어 상세 설명](#명령어-상세-설명)
  - [run](#run)
  - [validate](#validate)
  - [list](#list)
- [설정 파일 구조](#설정-파일-구조)
- [출력 형식](#출력-형식)
- [예제](#예제)

## 설치

Python 패키지로 설치하려면:

```bash
pip install s3tester
```

또는 소스 코드에서 직접 실행하려면:

```bash
git clone https://github.com/TaeyeongKwak/s3tester.git
cd s3tester
pip install -e .
```

## 기본 명령어

`s3tester`는 다음과 같은 주요 명령어를 제공합니다:

```bash
# 도움말 표시
s3tester --help

# 버전 정보 표시
s3tester --version

# 전역 로깅 옵션과 함께 실행
s3tester --log-level DEBUG --log-format json --log-file test.log [COMMAND]

# 테스트 실행
s3tester run --config <설정 파일 경로>

# 설정 파일 검증
s3tester validate --config <설정 파일 경로>

# 지원되는 작업 목록 표시
s3tester list --supported-operations
```

## 전역 옵션

모든 명령어에 사용할 수 있는 전역 옵션:

- `--log-level`: 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-format`: 로그 형식 설정 (standard, json)  
- `--log-file`: 로그 파일 경로 설정

**예시**:
```bash
# JSON 형식 로그를 파일에 저장하면서 디버그 레벨로 실행
s3tester --log-level DEBUG --log-format json --log-file debug.log run examples/simple-config.yaml

# 표준 형식 로그로 INFO 레벨 실행
s3tester --log-level INFO --log-format standard validate examples/simple-config.yaml
```

## 명령어 상세 설명

### run

테스트를 실행합니다.

```bash
s3tester run --config <설정 파일 경로> [옵션]
```

**옵션**:
- `--config`, `-c`: 테스트 설정 파일 경로 (필수)
- `--group`, `-g`: 실행할 특정 테스트 그룹 (여러 그룹을 지정하려면 여러 번 사용)
- `--output`, `-o`: 결과를 저장할 파일 경로
- `--format`, `-f`: 출력 형식 (`json`, `yaml`, `table`, `console` 중 하나, 기본값: `console`)
- `--parallel`, `-p`: 병렬로 테스트 실행 (설정 파일의 설정보다 우선)
- `--timeout`, `-t`: 각 작업의 제한 시간(초)
- `--dry-run`: 실제로 테스트를 실행하지 않고 설정만 검증
- `--verbose`, `-v`: 상세 출력 활성화

**예시**:
```bash
# 기본 실행
s3tester run -c examples/basic-operations.yaml

# JSON 형식으로 출력하고 결과를 파일에 저장
s3tester run -c examples/basic-operations.yaml -f json -o results.json

# 특정 그룹만 실행
s3tester run -c examples/all-tests.yaml -g bucket-operations -g object-operations
```

### validate

테스트 설정 파일을 검증합니다.

```bash
s3tester validate --config <설정 파일 경로> [옵션]
```

**옵션**:
- `--config`, `-c`: 검증할 테스트 설정 파일 경로 (필수)
- `--strict`: 엄격한 검증 적용 (경고도 오류로 처리)
- `--format`, `-f`: 출력 형식 (`json`, `yaml`, `table`, `console` 중 하나, 기본값: `console`)

**예시**:
```bash
# 기본 검증
s3tester validate -c examples/basic-operations.yaml

# 엄격한 검증
s3tester validate -c examples/advanced-tests.yaml --strict

# YAML 형식으로 검증 결과 출력
s3tester validate -c examples/complex-config.yaml -f yaml
```

### list

설정 구성 요소와 지원되는 작업을 나열합니다.

```bash
s3tester list [--config <설정 파일 경로>] [옵션]
```

**옵션**:
- `--config`, `-c`: 설정 파일 경로 (`--supported-operations`를 사용하지 않는 경우 필수)
- `--credentials`: 설정 파일에 정의된 자격 증명 목록 표시
- `--groups`: 설정 파일에 정의된 테스트 그룹 목록 표시
- `--operations`: 설정 파일에 정의된 테스트 작업 목록 표시
- `--supported-operations`: 지원되는 모든 S3 작업 목록 표시

**예시**:
```bash
# 지원되는 모든 S3 작업 나열 (설정 파일 필요 없음)
s3tester list --supported-operations

# 설정에 정의된 모든 구성 요소 나열 (자격 증명, 그룹, 작업)
s3tester list -c examples/complex-config.yaml

# 설정에 정의된 자격 증명만 나열
s3tester list -c examples/multi-account.yaml --credentials

# 설정에 정의된 테스트 그룹만 나열
s3tester list -c examples/complex-config.yaml --groups

# 설정에 정의된 모든 작업 나열 (그룹별로)
s3tester list -c examples/complex-config.yaml --operations
```

## 설정 파일 구조

`s3tester`는 YAML 형식의 설정 파일을 사용합니다. 기본 구조는 다음과 같습니다:

```yaml
# 전역 설정
config:
  # S3 엔드포인트 설정
  endpoint_url: https://s3.amazonaws.com
  region: us-east-1
  path_style: false  # false=virtual hosted style, true=path style
  
  # 자격 증명 목록
  credentials:
    - name: default
      access_key: YOUR_ACCESS_KEY
      secret_key: YOUR_SECRET_KEY
    - name: read-only
      access_key: READ_ONLY_ACCESS_KEY
      secret_key: READ_ONLY_SECRET_KEY

# 테스트 케이스 설정
test_cases:
  # 병렬 실행 설정 (선택 사항)
  parallel: false
  
  # 테스트 그룹 목록
  groups:
    - name: bucket-operations
      # 사용할 자격 증명 이름
      credential: default
      
      # 작업 순서와 단계 정의
      before:  # 사전 준비 작업
        - operation: CreateBucket
          parameters:
            Bucket: test-bucket
      
      test:  # 실제 테스트할 작업
        - operation: HeadBucket
          parameters:
            Bucket: test-bucket
          expected_result:
            success: true
      
      after:  # 정리 작업
        - operation: DeleteBucket
          parameters:
            Bucket: test-bucket
```

## 출력 형식

`s3tester`는 다음 출력 형식을 지원합니다:

- `console`: 터미널에 맞게 서식이 지정된 사용자 친화적인 출력 (기본값)
- `table`: 간단한 ASCII 테이블 형식
- `json`: JSON 형식 출력 (프로그래밍 방식 처리에 유용)
- `yaml`: YAML 형식 출력

## 예제

### 기본 버킷 작업 테스트

```bash
s3tester run -c examples/basic-bucket-operations.yaml
```

설정 파일:
```yaml
config:
  endpoint_url: http://localhost:9000
  region: us-east-1
  path_style: true
  credentials:
    - name: minio
      access_key: minioadmin
      secret_key: minioadmin

test_cases:
  groups:
    - name: basic-bucket-test
      credential: minio
      test:
        - operation: CreateBucket
          parameters:
            Bucket: test-bucket
        - operation: HeadBucket
          parameters:
            Bucket: test-bucket
        - operation: DeleteBucket
          parameters:
            Bucket: test-bucket
```

### 권한 및 정책 테스트

```bash
s3tester run -c examples/access-control-test.yaml
```

설정 파일:
```yaml
config:
  endpoint_url: http://localhost:9000
  region: us-east-1
  path_style: true
  credentials:
    - name: admin
      access_key: minioadmin
      secret_key: minioadmin
    - name: readonly
      access_key: readonlyuser
      secret_key: readonlypass

test_cases:
  groups:
    - name: bucket-policy-permissions-test
      credential: admin
      before:
        - operation: CreateBucket
          parameters:
            Bucket: policy-test-bucket
        - operation: PutObject
          parameters:
            Bucket: policy-test-bucket
            Key: restricted-object.txt
            Body: 이 객체는 정책으로 제한됩니다.
        - operation: PutBucketPolicy
          parameters:
            Bucket: policy-test-bucket
            Policy: |
              {
                "Version": "2012-10-17",
                "Statement": [
                  {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::policy-test-bucket/*"
                  },
                  {
                    "Effect": "Deny",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:PutObject", "s3:DeleteObject"],
                    "Resource": "arn:aws:s3:::policy-test-bucket/restricted-object.txt"
                  }
                ]
              }
      test:
        - operation: GetObject
          parameters:
            Bucket: policy-test-bucket
            Key: restricted-object.txt
        - operation: PutObject
          parameters:
            Bucket: policy-test-bucket
            Key: new-object.txt
            Body: 이 작업은 실패해야 합니다.
          expected_result:
            success: false
            error_code: AccessDenied
        - operation: DeleteObject
          parameters:
            Bucket: policy-test-bucket
            Key: restricted-object.txt
          expected_result:
            success: false
            error_code: AccessDenied
        - operation: PutObject
          parameters:
            Bucket: policy-test-bucket
            Key: unrestricted-object.txt
            Body: 이 작업은 허용되어야 합니다.
      after:
        - operation: DeleteObject
          parameters:
            Bucket: policy-test-bucket
            Key: unrestricted-object.txt
        - operation: DeleteObject
          parameters:
            Bucket: policy-test-bucket
            Key: restricted-object.txt
        - operation: DeleteBucketPolicy
          parameters:
            Bucket: policy-test-bucket
        - operation: DeleteBucket
          parameters:
            Bucket: policy-test-bucket
```

## 자세한 정보

더 많은 예제와 고급 사용법은 [GitHub 저장소](https://github.com/TaeyeongKwak/s3tester)를 참조하세요.

# S3 테스터 사용 가이드

이 문서는 S3 테스터 도구 사용 방법에 대한 가이드입니다.

## 설정

S3 테스터는 YAML 구성 파일을 사용하여 다양한 S3 작업을 테스트합니다. 테스트를 시작하기 전에 로컬 또는 원격 S3 호환 서비스(예: MinIO, AWS S3 등)가 실행 중인지 확인하세요.

### 사전 요구 사항

- Python 3.6 이상
- MinIO 또는 다른 S3 호환 서비스
- 필요한 Python 패키지 설치:
  ```
  pip install boto3 pyyaml
  ```

## 테스트 실행 방법

### 1. 테스트 데이터 생성

테스트 파일 업로드를 위한 테스트 데이터 생성:

```bash
bash ./examples/create-test-data.sh
```

### 2. 개별 테스트 실행

각 테스트 구성 파일은 특정 S3 기능을 테스트합니다:

```bash
# 확장 S3 작업 테스트
python -m s3tester run examples/extended-operations-test.yaml

# 파일 업로드 및 다운로드 테스트
python -m s3tester run examples/file-upload-test.yaml

# 권한 및 접근 제어 테스트
python -m s3tester run examples/access-control-test.yaml

# 성능 및 벤치마킹 테스트
python -m s3tester run examples/performance-test.yaml
```

### 3. 모든 테스트 실행

모든 테스트를 순차적으로 실행하는 스크립트:

```bash
bash ./examples/run-all-tests.sh
```

## 테스트 구성 파일 형식

테스트 구성 파일은 YAML 형식으로 작성되며 다음과 같은 구조를 가집니다:

```yaml
config:
  endpoint_url: "http://localhost:9000"  # S3 호환 서비스 엔드포인트
  region: "us-east-1"
  path_style: true  # Path style URL 사용 여부
  credentials:
    - name: "user-name"
      access_key: "access-key"
      secret_key: "secret-key"

test_cases:
  parallel: false  # 병렬 테스트 여부
  concurrency: 1  # 병렬 테스트 시 동시성 수준
  groups:
    - name: "test-group-name"
      credential: "user-name"
      before_test:  # 테스트 전 실행할 작업
        - operation: "OperationName"
          parameters:
            param1: "value1"
      
      test:  # 주요 테스트 작업
        - operation: "OperationName"
          parameters:
            param1: "value1"
          expected_result:
            success: true
      
      after_test:  # 테스트 후 정리 작업
        - operation: "OperationName"
          parameters:
            param1: "value1"
```

## 지원되는 S3 작업

- 버킷 작업: CreateBucket, DeleteBucket, ListBuckets, HeadBucket, GetBucketLocation, PutBucketVersioning, GetBucketVersioning, PutBucketTagging, GetBucketTagging, DeleteBucketTagging, PutBucketPolicy, GetBucketPolicy, DeleteBucketPolicy
- 객체 작업: PutObject, GetObject, DeleteObject, ListObjects, ListObjectsV2, HeadObject, CopyObject, ListObjectVersions
- 객체 태그 작업: PutObjectTagging, GetObjectTagging, DeleteObjectTagging
- 멀티파트 업로드: CreateMultipartUpload, UploadPart, CompleteMultipartUpload, AbortMultipartUpload
- 접근 제어: PutBucketAcl, GetBucketAcl, PutObjectAcl, GetObjectAcl
- 미리 서명된 URL: GetPresignedURL

## 성능 테스트

성능 테스트는 S3 작업의 성능을 측정하고 벤치마킹하는 데 사용됩니다. 구성 파일의 `metrics` 섹션에서 메트릭 수집을 활성화할 수 있습니다:

```yaml
metrics:
  capture: true  # 메트릭 수집 활성화
  prefix: "operation_name"  # 메트릭 이름 접두사
```

## 문제 해결

- 연결 오류: S3 호환 서비스가 실행 중이고 엔드포인트 URL이 올바른지 확인하세요.
- 인증 오류: 액세스 키와 비밀 키가 올바른지 확인하세요.
- 버킷 이름 충돌: 다른 테스트 실행 사이에 버킷 이름을 변경하거나 테스트 후 버킷을 정리하세요.

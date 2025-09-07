# S3Tester 설정 파일 참조

이 문서는 S3Tester의 설정 파일 형식에 대한 자세한 참조 정보를 제공합니다. 설정 파일은 YAML 형식으로 작성되며, 테스트 시나리오와 모든 테스트 매개변수를 정의합니다.

## 기본 구조

설정 파일은 두 개의 주요 섹션으로 구성됩니다:
1. `config`: 글로벌 설정 및 자격 증명
2. `test_cases`: 테스트 그룹 및 작업 정의

```yaml
config:
  # 글로벌 설정
  endpoint_url: https://s3.amazonaws.com
  region: us-east-1
  path_style: false
  
  # 자격 증명
  credentials:
    - name: default
      access_key: ACCESS_KEY
      secret_key: SECRET_KEY

test_cases:
  # 테스트 그룹
  parallel: false
  groups:
    - name: group-name
      # 테스트 작업
      ...
```

## 설정 섹션 (config)

### 기본 옵션

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `endpoint_url` | 문자열 | Y | S3 API 엔드포인트 URL |
| `region` | 문자열 | Y | AWS 리전 이름 (예: us-east-1) |
| `path_style` | 불리언 | N | 경로 스타일 URL 사용 여부 (기본값: false) |
| `timeout` | 정수 | N | 작업 제한 시간(초) (기본값: 30) |
| `retry_max_attempts` | 정수 | N | 최대 재시도 횟수 (기본값: 3) |
| `retry_mode` | 문자열 | N | 재시도 모드 (standard/adaptive/legacy) |

### 자격 증명

```yaml
credentials:
  - name: default
    access_key: ACCESS_KEY
    secret_key: SECRET_KEY
    session_token: SESSION_TOKEN  # 선택 사항
  - name: read-only
    access_key: RO_ACCESS_KEY
    secret_key: RO_SECRET_KEY
    endpoint_url: https://custom-endpoint.com  # 자격 증명별 엔드포인트 (선택 사항)
    region: eu-west-1  # 자격 증명별 리전 (선택 사항)
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `name` | 문자열 | Y | 자격 증명의 고유 이름 (테스트 그룹에서 참조) |
| `access_key` | 문자열 | Y | AWS 액세스 키 ID |
| `secret_key` | 문자열 | Y | AWS 시크릿 액세스 키 |
| `session_token` | 문자열 | N | 임시 자격 증명용 세션 토큰 |
| `endpoint_url` | 문자열 | N | 이 자격 증명에 대한 사용자 지정 엔드포인트 |
| `region` | 문자열 | N | 이 자격 증명에 대한 사용자 지정 리전 |

### 환경 변수

설정 파일에서 환경 변수를 사용할 수 있습니다:

```yaml
config:
  endpoint_url: ${S3_ENDPOINT_URL}
  credentials:
    - name: default
      access_key: ${AWS_ACCESS_KEY_ID}
      secret_key: ${AWS_SECRET_ACCESS_KEY}
```

기본값을 제공할 수도 있습니다:
```yaml
endpoint_url: ${S3_ENDPOINT_URL:-http://localhost:9000}
```

## 테스트 케이스 섹션 (test_cases)

### 기본 구조

```yaml
test_cases:
  parallel: false  # 테스트 그룹의 병렬 실행 여부
  groups:
    - name: group-1
      credential: default  # 사용할 자격 증명 이름
      
      # 선택적 단계: 테스트 전 실행
      before:
        - operation: CreateBucket
          parameters:
            Bucket: test-bucket
      
      # 필수 단계: 실제 테스트
      test:
        - operation: HeadBucket
          parameters:
            Bucket: test-bucket
          expected_result:
            success: true
      
      # 선택적 단계: 테스트 후 정리
      after:
        - operation: DeleteBucket
          parameters:
            Bucket: test-bucket
```

### 그룹 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `name` | 문자열 | Y | 그룹의 고유한 이름 |
| `credential` | 문자열 | Y | 사용할 자격 증명 이름 |
| `parallel` | 불리언 | N | 이 그룹 내에서 작업의 병렬 실행 여부 |
| `before` | 배열 | N | 테스트 전에 실행할 작업 목록 |
| `test` | 배열 | Y | 테스트할 작업 목록 |
| `after` | 배열 | N | 테스트 후에 실행할 정리 작업 목록 |

### 작업 필드

```yaml
- operation: PutObject
  parameters:
    Bucket: test-bucket
    Key: test-object.txt
    Body: This is a test object
  expected_result:
    success: true
    status_code: 200
    error_code: null
    response_contains:
      ETag: '"[0-9a-f]{32}"'  # 정규 표현식 지원
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `operation` | 문자열 | Y | S3 API 작업 이름 |
| `parameters` | 객체 | Y | 작업에 전달할 매개변수 |
| `expected_result` | 객체 | N | 예상 결과 (테스트 유효성 검사에 사용) |
| `debug` | 불리언 | N | 자세한 디버그 정보 활성화 (기본값: false) |

### 예상 결과 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `success` | 불리언 | N | 작업의 성공 여부 |
| `status_code` | 정수 | N | 예상 HTTP 상태 코드 |
| `error_code` | 문자열 | N | 예상 오류 코드 (실패 예상 시) |
| `response_contains` | 객체 | N | 응답에 포함되어야 하는 필드와 값 |

## 내장 변수

테스트 파일에서 다음과 같은 내장 변수를 사용할 수 있습니다:

- `${UUID}`: 무작위 UUID 생성
- `${TIMESTAMP}`: 현재 타임스탬프
- `${RANDOM_STRING:length}`: 지정된 길이의 무작위 문자열 생성

예시:
```yaml
- operation: CreateBucket
  parameters:
    Bucket: test-bucket-${UUID}
```

## 작업 간 데이터 공유

작업 간에 데이터를 공유하려면 `outputs`와 `inputs`를 사용합니다:

```yaml
- operation: CreateBucket
  parameters:
    Bucket: dynamic-bucket-${TIMESTAMP}
  outputs:
    bucket_name: parameters.Bucket

- operation: PutObject
  parameters:
    Bucket: ${inputs.bucket_name}
    Key: test-object.txt
    Body: This is a test object
```

## 전체 예시

```yaml
config:
  endpoint_url: http://localhost:9000
  region: us-east-1
  path_style: true
  
  credentials:
    - name: admin
      access_key: minioadmin
      secret_key: minioadmin

test_cases:
  groups:
    - name: lifecycle-test
      credential: admin
      
      before:
        - operation: CreateBucket
          parameters:
            Bucket: lifecycle-test-bucket
          outputs:
            bucket_name: parameters.Bucket
        
      test:
        - operation: PutBucketLifecycleConfiguration
          parameters:
            Bucket: ${inputs.bucket_name}
            LifecycleConfiguration:
              Rules:
                - ID: test-rule
                  Status: Enabled
                  Prefix: logs/
                  Expiration:
                    Days: 7
          
        - operation: GetBucketLifecycleConfiguration
          parameters:
            Bucket: ${inputs.bucket_name}
          expected_result:
            success: true
            response_contains:
              Rules:
                - ID: test-rule
                  Status: Enabled
      
      after:
        - operation: DeleteBucketLifecycle
          parameters:
            Bucket: ${inputs.bucket_name}
        
        - operation: DeleteBucket
          parameters:
            Bucket: ${inputs.bucket_name}
```

## 자세한 정보

각 S3 작업의 파라미터와 응답 형식에 대한 더 자세한 정보는 [AWS S3 API 참조](https://docs.aws.amazon.com/AmazonS3/latest/API/Welcome.html)를 참고하세요.

# 프로젝트 개요
AWS S3 호환 API를 테스트하기 위한 테스트 도구

# 요구사항
## 프로젝트
1. 프로젝트를 빌드하면 `s3tester`라는 이름의 binary 실행 파일이 생성.
1. 실행 파일은 `-c` 또는 `--config` 파라미터로 설정 파일 경로를 받아야 함.
1. 설정 파일은 `yaml` 형식으로 작성되어 있어야 하며, 자세한 형식은 아래 [설정 파일 형식](#설정-파일-형식)을 참고.
1. `--dry-run` 옵션을 통해 실제 테스트는 수행하지 않고, 설정 파일을 검증할 수 있어야 함.
1. 테스트 결과는 `stdout`으로 출력해야 함.
1. 테스트 결과는 각 그룹별로 출력되며, 그룹 이름, Operation, 입력 파라미터, 예상 결과, 실제 결과 등을 포함해야 함.
1. 네트워크 오류 등 예기치 못한 문제로 인해 실행 시 에러가 발생할 경우 에러 내용을 `stderr`로 출력해야 함.

## 설정 파일 형식

### 1. 전역 설정 (`config`)

#### 1.1 엔드포인트 설정
```yaml
config:
  endpoint-url: "https://s3.amazonaws.com"  # S3 엔드포인트 URL
  region: "us-east-1"                        # AWS 리전
  path_style: false                          # URL 스타일 (false: virtual-hosted, true: path-style)
```

#### 1.2 인증 정보 (`credentials`)
여러 개의 인증 정보를 정의하여 테스트 시나리오별로 다른 권한을 적용할 수 있습니다.

```yaml
credentials:
  - name: "FullAccess"              # 인증 정보 이름
    access_key: "ACCESS_KEY"        # AWS Access Key
    secret_key: "SECRET_KEY"        # AWS Secret Key
    session_token: ""                # (선택) Session Token
```

### 2. 테스트 케이스 (`test_cases`)

#### 2.1 실행 옵션
```yaml
test_cases:
  parallel: false  # true: 병렬 실행, false: 순차 실행
```

#### 2.2 테스트 그룹 (`groups`)
각 테스트 그룹은 관련된 테스트 케이스들을 묶어서 관리합니다.

```yaml
groups:
  - name: "그룹명"           # 테스트 그룹 이름
    credential: "인증정보명"   # 사용할 인증 정보
    before-test: [...]       # 테스트 전 실행할 작업
    test: [...]             # 실제 테스트 작업
    after-test: [...]       # 테스트 후 정리 작업
```

#### 2.3 Operation 정의
각 작업(operation)은 S3 API 호출을 정의합니다.

```yaml
- operation: "PutObject"        # S3 API 명령
  credential: "ReadOnly"        # (선택) 특정 operation에 대한 인증 정보 오버라이드
  parameters:                   # API 파라미터 (AWS CLI와 동일한 명칭 사용)
    bucket: "my-bucket"
    key: "file.dat"
    body: "file://path/to/file.dat"  # file:// prefix로 파일 경로 지정
  expected_result:              # 예상 결과
    success: true/false         # 성공/실패 여부
    error_code: "AccessDenied"  # (실패 시) S3 에러 코드
```

### 3. 외부 파일 포함 (`include`)
다른 설정 파일을 포함하여 테스트 케이스를 모듈화할 수 있습니다.

```yaml
include:
  - /path/to/another_cases.yaml
```

## 테스트 실행 흐름

1. **before-test**: 테스트 환경 준비 (예: 버킷 생성)
2. **test**: 실제 테스트 수행 및 결과 검증
3. **after-test**: 테스트 환경 정리 (예: 리소스 삭제)

## 주요 특징

### 권한 제어
- 전역 수준에서 그룹별로 다른 인증 정보 적용 가능
- Operation 수준에서 인증 정보 오버라이드 가능

### 파일 처리
- `file://` 접두어를 사용하여 로컬 파일 참조
- 대용량 파일 업로드 테스트 지원

### 결과 검증
- 성공/실패 여부 검증
- S3 에러 코드별 상세 검증

## 지원되는 S3 Operations
### 버킷 작업 (Bucket Operations)

#### 버킷 관리
- `CreateBucket` - 새 버킷 생성
- `DeleteBucket` - 빈 버킷 삭제
- `HeadBucket` - 버킷 존재 여부 및 접근 권한 확인
- `ListBuckets` - 모든 버킷 목록 조회

#### 버킷 정책 및 설정
- `GetBucketLocation` - 버킷의 리전 정보 조회
- `GetBucketVersioning` - 버킷 버전 관리 상태 조회
- `PutBucketVersioning` - 버킷 버전 관리 설정
- `ListBucketVersions` - 버킷의 객체 버전 목록 조회

### 객체 작업 (Object Operations)

#### 기본 객체 작업
- `PutObject` - 객체 업로드
- `GetObject` - 객체 다운로드
- `DeleteObject` - 객체 삭제
- `HeadObject` - 객체 메타데이터 조회
- `CopyObject` - 객체 복사

#### 객체 목록 조회
- `ListObjects` - 버킷의 객체 목록 조회 (v1)
- `ListObjectsV2` - 버킷의 객체 목록 조회 (v2)

#### 객체 버전 관리
- `GetObjectVersion` - 특정 버전의 객체 조회
- `DeleteObjectVersion` - 특정 버전의 객체 삭제

### 멀티파트 업로드 (Multipart Upload)

- `CreateMultipartUpload` - 멀티파트 업로드 시작
- `UploadPart` - 파트 업로드
- `UploadPartCopy` - 다른 객체로부터 파트 복사
- `CompleteMultipartUpload` - 멀티파트 업로드 완료
- `AbortMultipartUpload` - 멀티파트 업로드 취소
- `ListParts` - 업로드된 파트 목록 조회
- `ListMultipartUploads` - 진행 중인 멀티파트 업로드 목록 조회

### 객체 태깅 (Object Tagging)

- `GetObjectTagging` - 객체 태그 조회
- `PutObjectTagging` - 객체 태그 설정
- `DeleteObjectTagging` - 객체 태그 삭제
- `GetObjectVersionTagging` - 특정 버전 객체의 태그 조회
- `PutObjectVersionTagging` - 특정 버전 객체의 태그 설정
- `DeleteObjectVersionTagging` - 특정 버전 객체의 태그 삭제

### 버킷 태깅 (Bucket Tagging)

- `GetBucketTagging` - 버킷 태그 조회
- `PutBucketTagging` - 버킷 태그 설정
- `DeleteBucketTagging` - 버킷 태그 삭제

### 라이프사이클 관리 (Lifecycle Management)

- `GetBucketLifecycleConfiguration` - 버킷 라이프사이클 설정 조회
- `PutBucketLifecycleConfiguration` - 버킷 라이프사이클 설정
- `DeleteBucketLifecycle` - 버킷 라이프사이클 설정 삭제

### 정책 관리 (Policy Management)

- `GetBucketPolicy` - 버킷 정책 조회
- `PutBucketPolicy` - 버킷 정책 설정
- `DeleteBucketPolicy` - 버킷 정책 삭제
- `GetBucketPolicyStatus` - 버킷 정책 상태 조회

### 객체 잠금 (Object Lock)

- `GetObjectLockConfiguration` - 객체 잠금 설정 조회
- `PutObjectLockConfiguration` - 객체 잠금 설정
- `GetObjectRetention` - 객체 보존 설정 조회
- `PutObjectRetention` - 객체 보존 설정
- `GetObjectLegalHold` - 객체 법적 보존 상태 조회
- `PutObjectLegalHold` - 객체 법적 보존 설정

### CORS 설정

- `GetBucketCors` - 버킷 CORS 설정 조회
- `PutBucketCors` - 버킷 CORS 설정
- `DeleteBucketCors` - 버킷 CORS 설정 삭제

### 버킷 퍼블릭 엑세스 제어

- `GetPublicAccessBlock` - 버킷 퍼블릭 엑세스 제어 조회
- `PutPublicAccessBlock` - 버킷 퍼블릭 엑세스 제어 설정
- `DeletePublicAccessBlock` - 버킷 퍼블릭 엑세스 제어 삭제


## 예제 시나리오

### 1. 정상 업로드 테스트
```yaml
- name: "Upload Test"
  credential: "FullAccess"
  before-test:
    - operation: "CreateBucket"
      parameters:
        bucket: "test-bucket"
  test:
    - operation: "PutObject"
      parameters:
        bucket: "test-bucket"
        key: "test-file.dat"
        body: "file://./test-file.dat"
      expected_result:
        success: true
  after-test:
    - operation: "DeleteObject"
      parameters:
        bucket: "test-bucket"
        key: "test-file.dat"
    - operation: "DeleteBucket"
      parameters:
        bucket: "test-bucket"
```

### 2. 권한 검증 테스트
```yaml
- name: "Access Denied Test"
  credential: "ReadOnly"
  test:
    - operation: "PutObject"
      parameters:
        bucket: "existing-bucket"
        key: "file.dat"
        body: "file://./file.dat"
      expected_result:
        success: false
        error_code: "AccessDenied"
```

### 3. 전체 설정 파일 예시
```yaml
# 테스트 전역 설정
config:
  # 엔드 포인트
  endpoint-url: "https://s3.amazonaws.com"
  region: "us-east-1"
  path_style: false  # virtual-hosted-style vs path-style
  # 인증 정보 목록
  credentials:
    - name: "FullAccess"
      access_key: "AKIAIOSFODNN7EXAMPLE"
      secret_key: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
      session_token: ""  # optional
    - name: "ReadOnly"
      access_key: "AKIAIOSFODNN7EXAMPLE2"
      secret_key: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY2"

# 테스트 케이스
test_cases:
  parallel: false 테스트를 동시에 실행할 지 여부
  # 테스트 그룹
  groups:
    - name: "Upload Test" # 그룹 명칭
      credential: "FullAccess"  # 그룹에 적용할 자격 증명 이름
      before-test: # 테스트 전 실행할 operation 목록
        - operation: "CreateBucket"
          parameters: # 각 API별 설정 파라미터. 명칭은 aws cli와 동일
            bucket: "my-bucket"
      test: # 실제 테스트를 정의한 operation 목록
        - operation: "PutObject"
          parameters:
            bucket: "my-bucket"
            key: "file.dat"
            body: "file://path/to/file.dat"  # `file://` prefix for file path
            expected_result:
              success: true
      after-test: # 테스트 완료 후 실행할 operation 목록
        - operation: "DeleteObject"
          parameters:
            bucket: "my-bucket"
            key: "file.dat"
        - operation: "DeleteBucket"
          parameters:
            bucket: "my-bucket"
    - name: "Upload Object Fail (Access Denied)"
      credential: "ReadOnly" # 그룹에 적용할 자격 증명 이름
      test:
        - operation: "PutObject"
	      parameters:
            bucket: "existing-bucket"
            key: "file.dat"
	        body: "file://path/to/file.dat"	          
          expected_result:
            success: false
            error_code: "AccessDenied" # S3 error code
    - name: "Create Bucket And Upload Object Fail (Access Denied)"
      credential: "FullAccess"
      before-test:
	    - operation: "CreateBucket"
	      parameters:
	        bucket: "my-bucket"
      test:
        - operation: "PutObject"
          credential: "ReadOnly" # operation에 적용할 자격 증명 이름
	      parameters:
            bucket: "my-bucket"
            key: "file.dat"
	        body: "file://path/to/file.dat"	          
          expected_result:
            success: false
            error_code: "AccessDenied"

include: # 불러올 외부 설정 파일 경로
  - /path/to/another_cases.yaml  
```
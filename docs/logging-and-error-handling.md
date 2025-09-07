# 로깅 및 에러 처리 가이드

S3Tester v0.1.0은 향상된 로깅 시스템과 체계적인 에러 처리 기능을 제공합니다. 이 문서에서는 이러한 기능들을 효과적으로 활용하는 방법을 설명합니다.

## 목차

- [구조화된 로깅 시스템](#구조화된-로깅-시스템)
- [로그 레벨 및 설정](#로그-레벨-및-설정)
- [JSON 로깅 형식](#json-로깅-형식)
- [에러 처리 및 컨텍스트](#에러-처리-및-컨텍스트)
- [디버깅 가이드](#디버깅-가이드)
- [로그 분석 예제](#로그-분석-예제)

## 구조화된 로깅 시스템

S3Tester는 체계적인 로깅을 위한 중앙집중식 로깅 시스템을 제공합니다.

### 주요 특징

- **모듈별 로거**: 각 컴포넌트가 독립적인 로거를 사용
- **구조화된 데이터**: 로그에 컨텍스트 정보 포함
- **JSON 형식 지원**: 자동화된 로그 분석을 위한 구조화된 출력
- **성능 추적**: 작업 시간 및 메트릭 자동 기록

### 로거 네이밍 규칙

```
s3tester.{module}.{component}
```

예시:
- `s3tester.core.engine`: 테스트 실행 엔진
- `s3tester.operations.PutObject`: PutObject 작업
- `s3tester.integration.facade`: 통합 파사드
- `s3tester.cli`: CLI 인터페이스

## 로그 레벨 및 설정

### 지원하는 로그 레벨

| 레벨 | 설명 | 언제 사용 |
|------|------|----------|
| **DEBUG** | 상세한 디버그 정보 | 개발, 문제 해결 |
| **INFO** | 일반적인 정보성 메시지 | 기본 실행 상황 |
| **WARNING** | 경고 메시지 | 잠재적 문제 상황 |
| **ERROR** | 오류 메시지 | 실행 실패, 예외 발생 |
| **CRITICAL** | 심각한 오류 | 시스템 전체 실패 |

### 로그 레벨 설정 방법

```bash
# 명령줄에서 설정
s3tester --log-level DEBUG run examples/simple-config.yaml

# 환경 변수로 설정 (향후 지원 예정)
export S3TESTER_LOG_LEVEL=DEBUG
s3tester run examples/simple-config.yaml
```

### 로그 형식 옵션

#### Standard 형식 (기본)
```
2025-09-07 15:52:19,134 [    INFO] s3tester.core.validator: Configuration validation passed
```

#### JSON 형식
```bash
s3tester --log-format json run examples/simple-config.yaml
```

```json
{
  "timestamp": "2025-09-07 15:52:19,134",
  "level": "INFO",
  "logger": "s3tester.core.validator",
  "message": "Configuration validation passed",
  "module": "validator",
  "function": "validate_configuration", 
  "line": 54
}
```

## JSON 로깅 형식

JSON 로깅은 자동화된 로그 분석, 모니터링, 그리고 대시보드 구축에 유용합니다.

### 기본 JSON 구조

```json
{
  "timestamp": "ISO 형식 시간",
  "level": "로그 레벨",
  "logger": "로거 이름",
  "message": "메시지",
  "module": "모듈명",
  "function": "함수명",
  "line": "라인 번호"
}
```

### 작업별 구조화된 로그

#### 작업 시작 로그
```json
{
  "timestamp": "2025-09-07 15:52:19,200",
  "level": "INFO", 
  "logger": "s3tester.operations.PutObject",
  "message": "Starting PutObject",
  "operation": "PutObject",
  "context": {
    "bucket": "test-bucket",
    "key": "test-file.txt"
  }
}
```

#### 작업 성공 로그
```json
{
  "timestamp": "2025-09-07 15:52:19,350",
  "level": "INFO",
  "logger": "s3tester.operations.PutObject", 
  "message": "PutObject completed successfully in 0.15s",
  "operation": "PutObject",
  "duration": 0.15,
  "status": "success"
}
```

#### 작업 실패 로그
```json
{
  "timestamp": "2025-09-07 15:52:19,450",
  "level": "ERROR",
  "logger": "s3tester.operations.PutObject",
  "message": "PutObject failed: NoSuchBucket", 
  "operation": "PutObject",
  "duration": 0.25,
  "status": "error",
  "error_type": "ClientError",
  "error_message": "The specified bucket does not exist"
}
```

## 에러 처리 및 컨텍스트

### 체계적인 에러 처리

S3Tester는 다양한 레벨의 에러 처리를 제공합니다:

1. **Configuration Error**: 설정 파일 관련 오류
2. **Operation Error**: S3 API 작업 관련 오류  
3. **Execution Error**: 테스트 실행 엔진 오류
4. **Validation Error**: 입력 검증 오류

### 에러 컨텍스트 정보

각 에러는 다음과 같은 컨텍스트 정보를 포함합니다:

```json
{
  "error_type": "ConfigurationError",
  "error_message": "Invalid bucket name format",
  "operation": "CreateBucket", 
  "group_name": "bucket-operations",
  "parameters": {
    "bucket": "invalid..bucket..name"
  },
  "traceback": "최근 3개 프레임의 스택 트레이스"
}
```

### 사용자 친화적인 에러 메시지

#### 버킷 이름 검증 오류
```
❌ Bucket name 'my..invalid..bucket' contains consecutive periods
✅ 올바른 형식: 'my-valid-bucket'
```

#### 엔드포인트 URL 오류
```
❌ Endpoint URL 'localhost:9000' must start with 'http://' or 'https://'
✅ 올바른 형식: 'http://localhost:9000'
```

## 디버깅 가이드

### 일반적인 디버깅 워크플로우

1. **기본 실행으로 문제 확인**
```bash
s3tester run examples/simple-config.yaml
```

2. **상세 로그로 재실행**
```bash
s3tester --log-level DEBUG run examples/simple-config.yaml
```

3. **JSON 로그로 구조화된 정보 수집**
```bash
s3tester --log-level DEBUG --log-format json --log-file debug.log run examples/simple-config.yaml
```

4. **로그 분석**
```bash
# 에러 로그만 필터링
jq 'select(.level == "ERROR")' debug.log

# 특정 작업의 로그만 필터링  
jq 'select(.operation == "PutObject")' debug.log

# 실행 시간이 긴 작업 찾기
jq 'select(.duration and (.duration > 1.0))' debug.log
```

### 자주 발생하는 문제들

#### 1. 연결 오류
**증상**: `Could not connect to the endpoint URL`

**디버깅**:
```bash
# 연결 관련 디버그 로그 확인
s3tester --log-level DEBUG run config.yaml 2>&1 | grep -i "connect\|endpoint"
```

**해결책**:
- 엔드포인트 URL 확인
- 네트워크 연결 상태 확인
- 방화벽 설정 확인

#### 2. 권한 오류
**증상**: `AccessDenied` 에러

**디버깅**:
```bash  
# 권한 관련 로그 확인
jq 'select(.error_message | contains("AccessDenied"))' debug.log
```

**해결책**:
- 자격증명 확인
- 버킷 정책 검토
- IAM 권한 확인

#### 3. 구성 오류
**증상**: `Configuration validation failed`

**디버깅**:
```bash
# 구성 검증 상세 실행
s3tester --log-level DEBUG validate examples/simple-config.yaml --strict
```

## 로그 분석 예제

### 성능 분석

```bash
# 평균 실행 시간 계산
jq -r 'select(.duration) | .duration' debug.log | awk '{sum+=$1; count++} END {print "평균:", sum/count, "초"}'

# 가장 느린 작업 찾기
jq -r 'select(.duration) | "\(.duration)\t\(.operation)"' debug.log | sort -nr | head -5
```

### 성공률 분석

```bash
# 성공/실패 통계
jq -r 'select(.status) | .status' debug.log | sort | uniq -c

# 작업별 성공률
jq -r 'select(.status and .operation) | "\(.operation)\t\(.status)"' debug.log | \
  sort | uniq -c | awk '{print $2, $3, $1}'
```

### 에러 패턴 분석

```bash
# 가장 자주 발생하는 에러
jq -r 'select(.error_type) | .error_type' debug.log | sort | uniq -c | sort -nr

# 에러 발생 시간대 분석  
jq -r 'select(.level == "ERROR") | .timestamp' debug.log | cut -d' ' -f2 | cut -d: -f1 | sort | uniq -c
```

## 모니터링 및 알림 통합

### ELK 스택과 통합

```bash
# JSON 로그를 Elasticsearch로 전송
s3tester --log-format json run config.yaml | \
  while read line; do
    curl -X POST "localhost:9200/s3tester-logs/_doc" \
         -H "Content-Type: application/json" \
         -d "$line"
  done
```

### Prometheus 메트릭 추출 (향후 지원 예정)

```bash
# 성공률 메트릭
echo "s3tester_success_rate $(jq -s 'map(select(.status == "success")) | length / length' debug.log)"

# 평균 응답시간 메트릭  
echo "s3tester_avg_duration $(jq -s 'map(select(.duration) | .duration) | add / length' debug.log)"
```

## 베스트 프랙티스

### 1. 로그 레벨 선택

- **운영 환경**: INFO 레벨
- **문제 해결**: DEBUG 레벨  
- **성능 테스트**: WARNING 레벨 (불필요한 출력 최소화)

### 2. 로그 파일 관리

```bash
# 날짜별 로그 파일
s3tester --log-file "s3test-$(date +%Y%m%d).log" run config.yaml

# 로그 로테이션 (logrotate 사용)
echo '/var/log/s3tester/*.log {
    daily
    missingok
    rotate 30
    compress
    create 0644 user group
}' > /etc/logrotate.d/s3tester
```

### 3. 자동화 스크립트에서 활용

```bash
#!/bin/bash

LOG_FILE="s3test-$(date +%Y%m%d-%H%M%S).log"

# JSON 형식으로 로그 저장
s3tester --log-format json --log-file "$LOG_FILE" run "$1"

# 실패한 작업이 있는지 확인
FAILURES=$(jq -s 'map(select(.status == "error")) | length' "$LOG_FILE")

if [ "$FAILURES" -gt 0 ]; then
    echo "❌ $FAILURES개의 작업이 실패했습니다"
    jq -r 'select(.status == "error") | "\(.operation): \(.error_message)"' "$LOG_FILE"
    exit 1
else
    echo "✅ 모든 테스트가 성공했습니다"
    exit 0
fi
```

이 문서를 통해 S3Tester의 강력한 로깅 및 에러 처리 기능을 최대한 활용하실 수 있습니다.
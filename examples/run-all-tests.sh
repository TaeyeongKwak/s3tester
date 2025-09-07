#!/bin/bash
# S3 테스트 스크립트

# 기본 설정
ENDPOINT="http://localhost:9000"
ACCESS_KEY="minioadmin"
SECRET_KEY="minioadmin"
REGION="us-east-1"

# 색상 설정
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 테스트 데이터 생성
echo -e "${YELLOW}테스트 데이터 생성 중...${NC}"
bash ./examples/create-test-data.sh

# MinIO/S3 서비스가 실행 중인지 확인
echo -e "${YELLOW}S3 서비스 연결 확인 중...${NC}"
if ! curl -s --connect-timeout 5 $ENDPOINT > /dev/null; then
  echo -e "${RED}에러: S3 서비스(${ENDPOINT})에 연결할 수 없습니다. MinIO 또는 S3 호환 서비스가 실행 중인지 확인하세요.${NC}"
  exit 1
fi

# 테스트 실행
run_test() {
  local test_file=$1
  local test_name=$2
  
  echo -e "${YELLOW}${test_name} 실행 중...${NC}"
  python -m s3tester run $test_file
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}${test_name} 테스트 성공!${NC}"
    return 0
  else
    echo -e "${RED}${test_name} 테스트 실패!${NC}"
    return 1
  fi
}

# 모든 테스트 실행
echo -e "${YELLOW}모든 테스트 시작...${NC}"

# 기본 작업 테스트
run_test "./examples/extended-operations-test.yaml" "확장 작업 테스트"

# 파일 업로드 테스트
run_test "./examples/file-upload-test.yaml" "파일 업로드 테스트"

# 접근 제어 테스트
run_test "./examples/access-control-test.yaml" "접근 제어 테스트"

# 성능 테스트는 선택적으로 실행 (오래 걸릴 수 있음)
read -p "성능 테스트를 실행하시겠습니까? (y/n): " run_perf
if [ "$run_perf" = "y" ]; then
  run_test "./examples/performance-test.yaml" "성능 테스트"
fi

echo -e "${GREEN}모든 테스트가 완료되었습니다!${NC}"

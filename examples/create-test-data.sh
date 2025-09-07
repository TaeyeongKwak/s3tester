#!/bin/bash
# 테스트 데이터 파일 생성

mkdir -p test-data
echo "이것은 테스트 데이터 파일입니다." > test-data/sample.txt
echo "이것은 다른 테스트 데이터 파일입니다." > test-data/sample2.txt

# 이진 데이터 생성 (100KB)
dd if=/dev/urandom of=test-data/binary-data.bin bs=1024 count=100

echo "테스트 데이터 파일이 생성되었습니다."

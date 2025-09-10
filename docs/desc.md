바이브 코딩에 대한 가이드라인이라기보단 제가 어떤 식으로 바이브 코딩을 수행했고, 어떤 결과물이 나왔는지를 보여드리고자 하였습니다.
# 바이브 코딩?
* 개발자가 생성형 인공지능의 도움을 받아 코드를 작성하는 행위
- 직감과 느낌에 의존한다는 의미로 바이브 코딩이라는 이름이 붙음

바이브 코딩은 아래와 같이 여러 단계가 존재.

| 레벨  | AI 역할                                | 개발자 역할                |
| --- | ------------------------------------ | --------------------- |
| 1   | 단순 보조, 함수 수준 코드 자동 완성                | 코드 작성의 주도권 유지         |
| 2   | 파일 단위의 반복 작업이나 간단한 스크립트 자동 완성        | 코드 검토 및 소규모 수정        |
| 3   | 독립적인 기능 모듈을 설계 및 제안                  | 모듈 통합 및 관리, 설계, 검토 역할 |
| 4   | 프로젝트 수준으로 전반적인 지원(설계, 리팩토링, 테스트, 배포) | 요구 사항 정의 및 산출물 검토     |
| 5   | 비즈니스 목표와 운영 환경까지 자동화                 | 전략 수립 및 핵심 의사 결정      |

기존에는 1-2 단계 수준의 바이브 코딩을 진행했지만, 이번에는 3-4 단계 수준으로 체험해볼 예정

# 시작 이유
* 개발해보고 싶은 것들은 많은데 실제 코딩을 진행하는 것은 많은 시간이 소요.
* AI가 과연 얼마나 생산성을 올려줄 수 있을 지 궁금

# 무엇을 만들까?
다양한 주제 고민
- 쿠버네티스 호환 CNI 플러그인
- Rust 기반 API Gateway 솔루션
- 간단한 Object Storage 솔루션
- AWS S3 API 테스트 툴
- ...

최종적으로 **AWS S3 API 테스트 툴** 개발을 진행하기로 결정
### 선정 이유
1. 업무에 도움이 될 수 있는 프로젝트를 개발하고 싶었음.
2. 생각나는 후보들 중에서 가장 난이도가 낮아보임
3. 자료가 상대적으로 많을 것이라고 예상됨
4. 기능이 직관적이고 테스트 환경을 구성하기 쉬움

# 어떻게 시작하지?
구글링을 통해 여러 블로그 및 레딧을 탐방하던 중 [AWS Vibe Coding Guide](https://awslabs.github.io/mcp/vibe_coding/)를 발견

이 가이드 문서를 기반으로 여러 글을 종합해본 결과 일반적으로 아래와 같은 workflow를 통해 바이브 코딩을 수행하는 것으로 확인.

1. 요구사항을 기반으로 AI가 참고할 요구 사항 및 아키텍처 문서 생성
2. 생성된 문서를 기반으로 작업을 분할하고 이를 문서화
3. 분할된 작업 단위로 개발 진행
4. 개발이 완료된 부분에 대한 테스트
5. (3-4) 반복
6. 1차 개발이 완료되었다면 실제 테스트
7. 부족한 부분 수정 요청
8. 다시 반복

# 도구 선택
### AI 에이전트
![[Pasted image 20250908210632.png]]

구글링을 통한 성능 조사 및 주위 개발자 사용 후기를 기반으로 [Claude Code](https://www.anthropic.com/claude-code)를 선택

하지만 실제 작업 도중 토큰 부족으로 인한 시간 지연이 너무 심해서 **Github Copilot**을 병행하여 사용.

### MCP 활용
환각을 방지하기 위해 사용하는 의존성에 대한 Context를 제공하는 MCP 위주로 선택
- https://gitmcp.io/
- https://gitingest.com/

# 바이브 코딩 시작
### 요구사항 정리
프로젝트를 시작하기 위해 [요구사항 문서](https://github.com/TaeyeongKwak/s3tester/blob/master/specify.md)를 작성

이를 기반으로 다른 설계 문서들을 어떻게 생성할까 고민하던 중 [Spec Driven Development](https://news.hada.io/topic?id=22938)라는 방법론을 발견. 

간단히 확인해보았을 때 괜찮아보여 해당 방법론을 적용해보기로 결정

위 문서에서는 [Kiro](https://kiro.dev/)라는 IDE를 소개하였는데 이 IDE를 제대로 사용하려면 유료 플랜을 사용해야하는 것으로 확인됨.

더 찾아보던 중 github에서 제공하는 [spec-kit](https://github.com/github/spec-kit)이라는 툴이 있는 것을 발견
Claude Code 및 Github Copilot과 호환되며, 사용법이 간단하여 이 툴을 사용해보기로 결정

### spec-kit

- 프로젝트 초기화 시 아래와 같은 문서 생성
```
$ uvx --from git+https://github.com/github/spec-kit.git specify init --here --ai claude
$ tree
...
⎿  .
     ├── memory
     │   ├── constitution.md
     │   └── constitution_update_checklist.md
     ├── scripts
     │   ├── check-task-prerequisites.sh
     │   ├── common.sh
     │   ├── create-new-feature.sh
     │   ├── get-feature-paths.sh
     │   ├── setup-plan.sh
     │   └── update-agent-context.sh
     └── templates
         ├── agent-file-template.md
         ├── plan-template.md
         ├── spec-template.md
         └── tasks-template.md
```

- 사양 문서 생성
```
> /specify AWS S3 API 호환성 테스트를 위한 테스트 도구인 s3tester를 개발할거야. 자세한 사양은 @specify.md 를 참고해줘.
```
https://github.com/TaeyeongKwak/s3tester/blob/master/specs/002-aws-s3-api/spec.md

- 계획 및 설계 문서 생성
```
/plan 이 프로젝트를 개발하기 위한 프로그래밍 언어는 python을 사용한다. AWS S3 API를 호출하기 위한 의존성은 [boto3](https://github.com/boto/boto3) 를 사용한다. 병렬 처리를 위한 의존성은 `asyncio`를 사용한다. 테스트 프레임워크는 `pytest`를 사용한다. 설정 파일을 검증할 때는 `jsonschema`를 사용한다.
```
https://github.com/TaeyeongKwak/s3tester/blob/master/specs/002-aws-s3-api/plan.md

```
/tasks
```
https://github.com/TaeyeongKwak/s3tester/blob/master/specs/002-aws-s3-api/tasks.md

기본 문서 생성이 완료되었으니 이를 기반으로 실제 구현 작업 진행

## 구현
구현은 아래와 같은 방식으로 진행

### 구현 전 계획 요청
AI는 가끔 예기치 못한 행위를 수행하는 경우가 존재하기 때문에 실제 작업 전에 계획을 세우도록 요청하는 것이 중요함. 
Claude Code에는 실제 코드를 작성하지 않고 먼저 계획을 작성하는 Plan Mode가 존재하기에 이를 활용

![[Pasted image 20250908221809.png]]

위와 같은 계획 확인 후 문제가 없다면 진행, 문제가 있다면 취소 후 다시 대화 진행

### 구현 진행
실제 구현을 진행할 때 Claude Code는 자신이 진행할 작업에 대해 preview를 제공하기 때문에 이를 한번 확인하고 유효한 작업인지 확인하는 것도 중요함.

![[Pasted image 20250908224219.png]]

### 단위 테스트
AI가 작성한 코드를 한번씩 검토하더라도 놓치는 부분이 분명 존재할 수 있음. 그렇기에 중요 로직에 대해서는 단위 테스트를 생성을 요청하여 한번 더 잘못된 로직을 필터링하는 것이 효과적임.
```
> @src/s3tester/operations/object.py 에 대한 테스트 코드를 작성하자. 먼저 이 코드를 테스트하기 위한 테스트 케이스를 정리해줘.
...
●User approved Claude's plan:
  ⎿  Object Operations 테스트 코드 구현 계획

     📋 구현할 테스트 파일들

     1. tests/unit/operations/conftest.py - 공통 Fixtures

     - mock_s3_client: boto3 S3 클라이언트 mock
     - temp_config_dir: 임시 설정 디렉토리
     - sample_files: 테스트용 파일들 (텍스트, 바이너리)
     - operation_context_factory: OperationContext 생성 helper

     2. tests/unit/operations/test_object_operations.py - 메인 테스트 파일

     PutObjectOperation (18개 테스트):
     - 매개변수 검증: 필수 매개변수, body 처리, 선택적 매개변수
     - 실행 테스트: 성공 케이스, 오류 처리 (NoSuchBucket, AccessDenied 등)

     GetObjectOperation (12개 테스트):
     - 매개변수 검증: 필수/선택적 매개변수 테스트
     - 실행 테스트: 성공, Body 읽기, 오류 처리

     DeleteObjectOperation (10개 테스트):
     - 매개변수 검증 및 실행 테스트
     - S3 특성 고려 (존재하지 않는 키 삭제도 성공)

     HeadObjectOperation (10개 테스트):
     - 메타데이터 조회 성공/실패 케이스

     🛠️ 주요 특징

     Mock 전략:

     - boto3.client 완전 mock으로 실제 S3 호출 없음
     - ClientError 시뮬레이션으로 오류 시나리오 테스트
     - FileReference를 위한 임시 파일 시스템 사용

     테스트 커버리지:

     - 매개변수 검증: 모든 필수/선택적 매개변수 검증
     - 성공 케이스: 정상 작동 확인
     - 오류 처리: S3 오류 코드별 적절한 처리 확인
     - 파일 처리: file:// URL, FileReference 객체 처리

     품질 보장:

     - 실제 object.py 구현과 정확히 일치하는 테스트
     - 기존 test_operations.py의 패턴 유지
     - pytest fixtures 활용으로 테스트 코드 재사용성 극대화

     총 50개의 포괄적인 테스트 케이스로 object.py의 모든 기능을 검증합니다.
```

```
> 계획대로 테스트 코드를 작성하고 테스트를 수행해줘.
...
  ✅ Object Operations 테스트 완료!

  성과 요약:

  📊 테스트 결과

  - 총 46개 테스트 모두 성공 (100% 통과)
  - 실행 시간: 0.21초로 매우 빠름
  - 커버리지: 4개 주요 클래스 완전 테스트

  🧪 구현된 테스트 분류

  1. PutObjectOperation (17개 테스트)
  - ✅ 매개변수 검증: 필수/선택적 매개변수, 파일 처리
  - ✅ 실행 테스트: 성공 케이스, 다양한 S3 오류 상황

  2. GetObjectOperation (11개 테스트)
  - ✅ 매개변수 검증: bucket/key 필수, version_id/range 선택적
  - ✅ 실행 테스트: Body 스트림 읽기, 오류 처리

  3. DeleteObjectOperation (9개 테스트)
  - ✅ 매개변수 검증 및 실행 테스트
  - ✅ S3 특성 반영 (존재하지 않는 키 삭제도 성공)

  4. HeadObjectOperation (9개 테스트)
  - ✅ 메타데이터 조회 성공/실패 시나리오

  🛠️ 테스트 품질 특징

  Mock 전략:
  - boto3.client 완전 mock으로 실제 S3 호출 없음
  - 다양한 ClientError 시나리오 시뮬레이션
  - 파일 시스템 mock으로 FileReference 테스트

  커버리지:
  - 모든 매개변수 검증 로직 테스트
  - S3 오류 코드별 적절한 처리 확인
  - 파일 처리 (file:// URL, FileReference) 완전 테스트

  로그 출력 확인:
  - 테스트 실행 중 적절한 로그 메시지 출력
  - 오류 상황에서 명확한 오류 로그 생성

  📁 생성된 파일들

  tests/unit/operations/
  ├── __init__.py                    # 패키지 초기화
  ├── conftest.py                    # 공통 fixtures (모든 mock 설정)
  └── test_object_operations.py      # 46개 테스트 케이스

  이제 src/s3tester/operations/object.py의 모든 기능이 포괄적으로 테스트되어 있으며, 향후 코드 변경 시 안전하게 리팩토링할 수 있는 견고한 테스트 기반이 구축되었습니다!
```
### Commit
구현을 진행하다보면 전에 개발했던 코드에 문제가 발생하여 코드를 되돌려야하는 경우가 존재할 수 있음. 
하지만 Claude Code는 작업 되돌리기 기능이 없는 것으로 보이기에 이를 수동으로라도 처리하기 위해 git을 활용하는게 거의 필수적임.

아래와 같이 Claude Code에 commit을 요청할 수 있음.
```
> @specs\002-aws-s3-api\tasks.md 현재 완료된 `Phase 3.1: Setup` 작업의 변경 사항을 git에 `Conventional Commits` 형식으로 commit 해줘.
```

![[Pasted image 20250908232430.png]]

## 테스트 및 수정
spec-kit을 사용하면 템플릿에 따라서 TDD 기반 Contract 테스트와 Integration 테스트가 먼저 작성되며, TASK의 종료는 이 모든 테스트가 통과되는 코드를 작성하는 것으로 마무리됨.

하지만 개발이 완료되었다고 하더라도 아래와 같은 케이스로 인해 실제로 프로젝트가 동작을 하지 않는 경우가 존재.

* 유효하지 않은 테스트 케이스
* 테스트만 통과하기 위한 하드 코딩
* 잘 개발해둔 코드를 사용하지 않고 실제로는 다른 코드를 호출

그렇기에 실제로 개발된 결과물을 실행해보면서 의도치 않은 에러를 방지하는 것이 중요.
# 결과물
https://github.com/TaeyeongKwak/s3tester

## 실제 사용
- 지원 operation
```
$ s3tester list --supported-operations
...
Supported S3 Operations:
  - AbortMultipartUpload
  - CompleteMultipartUpload
  - CopyObject
  - CreateBucket
  - CreateMultipartUpload
  - DeleteBucket
  - DeleteBucketPolicy
  - DeleteBucketTagging
  - DeleteObject
  - DeleteObjectTagging
  - GetBucketLocation
  - GetBucketPolicy
  - GetBucketTagging
  - GetBucketVersioning
  - GetObject
  - GetObjectTagging
  - HeadBucket
  - HeadObject
  - ListBuckets
  - ListObjectVersions
  - ListObjectsV2
  - ListParts
  - PutBucketPolicy
  - PutBucketTagging
  - PutBucketVersioning
  - PutObject
  - PutObjectTagging
  - UploadPart
```
- 설정 파일 검증
https://github.com/TaeyeongKwak/s3tester/blob/master/examples/access-control-test.yaml
```
$ s3tester validate --config examples/access-control-test.yaml
...
2025-09-08 22:54:54,112 [    INFO] s3tester.core.validator: Configuration validation passed (validator.py:54)
Configuration is valid. Found:
- 2 credential sets
- 1 test groups
- 11 total operations
```
- 테스트 수행
```
$ s3tester run --config examples/access-control-test.yaml --format table
...
2025-09-08 22:53:10,472 [    INFO] s3tester.core.validator: Configuration validation passed (validator.py:54)
Starting tests with 1 groups...
2025-09-08 22:53:10,473 [    INFO] s3tester.core.engine: Starting test session 4b44c56e-a74c-461e-9e17-c969dd371f12 (engine.py:90)
2025-09-08 22:53:10,473 [    INFO] s3tester.core.engine: Executing 1 groups sequentially (engine.py:152)
2025-09-08 22:53:10,473 [    INFO] s3tester.core.engine.bucket-policy-permissions-test: Starting test group: bucket-policy-permissions-test (engine.py:162)
2025-09-08 22:53:13,435 [    INFO] s3tester.core.engine.bucket-policy-permissions-test: Executing 3 before-test operations (engine.py:173)
2025-09-08 22:53:13,435 [    INFO] s3tester.core.engine: Executing operation CreateBucket sequentially... (engine.py:232)
2025-09-08 22:53:13,435 [    INFO] s3tester.operations.CreateBucket: Starting CreateBucket (logging_config.py:162)
2025-09-08 22:53:13,451 [    INFO] s3tester.operations.CreateBucket: CreateBucket completed successfully in 0.02s (logging_config.py:175)
2025-09-08 22:53:13,451 [    INFO] s3tester.core.engine: ✅ bucket-policy-permissions-test > CreateBucket (pass) [0.02s] (engine.py:346)
2025-09-08 22:53:13,451 [    INFO] s3tester.core.engine: Executing operation PutObject sequentially... (engine.py:232)
2025-09-08 22:53:13,451 [    INFO] s3tester.operations.PutObject: Starting PutObject (logging_config.py:162)
2025-09-08 22:53:13,463 [    INFO] s3tester.operations.PutObject: PutObject completed successfully in 0.01s (logging_config.py:175)
2025-09-08 22:53:13,463 [    INFO] s3tester.core.engine: ✅ bucket-policy-permissions-test > PutObject (pass) [0.01s] (engine.py:346)
2025-09-08 22:53:13,463 [    INFO] s3tester.core.engine: Executing operation PutBucketPolicy sequentially... (engine.py:232)
2025-09-08 22:53:13,463 [    INFO] s3tester.operations.PutBucketPolicy: Starting PutBucketPolicy (logging_config.py:162)
2025-09-08 22:53:13,485 [    INFO] s3tester.operations.PutBucketPolicy: PutBucketPolicy completed successfully in 0.02s (logging_config.py:175)
2025-09-08 22:53:13,485 [    INFO] s3tester.core.engine: ✅ bucket-policy-permissions-test > PutBucketPolicy (pass) [0.02s] (engine.py:346)
2025-09-08 22:53:13,485 [    INFO] s3tester.core.engine: Phase before completed with 3/3 successful operations (engine.py:264)
2025-09-08 22:53:13,485 [    INFO] s3tester.core.engine.bucket-policy-permissions-test: Executing 4 test operations (engine.py:184)
2025-09-08 22:53:13,485 [    INFO] s3tester.core.engine: Executing operation GetObject sequentially... (engine.py:232)
2025-09-08 22:53:16,230 [    INFO] s3tester.operations.GetObject: Starting GetObject (logging_config.py:162)
2025-09-08 22:53:16,235 [    INFO] s3tester.operations.GetObject: GetObject completed successfully in 0.01s (logging_config.py:175)
2025-09-08 22:53:16,235 [    INFO] s3tester.core.engine: ✅ bucket-policy-permissions-test > GetObject (pass) [0.01s] (engine.py:346)
2025-09-08 22:53:16,236 [    INFO] s3tester.core.engine: Executing operation PutObject sequentially... (engine.py:232)
2025-09-08 22:53:16,236 [    INFO] s3tester.operations.PutObject: Starting PutObject (logging_config.py:162)
2025-09-08 22:53:16,238 [   ERROR] s3tester.operations.PutObject: PutObject failed: AccessDenied - Access Denied. (object.py:90)
2025-09-08 22:53:16,238 [   ERROR] s3tester.operations.PutObject: PutObject failed: Access Denied. (logging_config.py:202)
NoneType: None
2025-09-08 22:53:16,238 [    INFO] s3tester.core.engine: ✅ bucket-policy-permissions-test > PutObject (pass) [0.00s] (engine.py:346)
2025-09-08 22:53:16,238 [    INFO] s3tester.core.engine: Executing operation DeleteObject sequentially... (engine.py:232)
2025-09-08 22:53:16,238 [    INFO] s3tester.operations.DeleteObject: Starting DeleteObject (logging_config.py:162)
2025-09-08 22:53:16,240 [   ERROR] s3tester.operations.DeleteObject: DeleteObject failed: AccessDenied - Access Denied. (object.py:215)
2025-09-08 22:53:16,240 [   ERROR] s3tester.operations.DeleteObject: DeleteObject failed: Access Denied. (logging_config.py:202)
NoneType: None
2025-09-08 22:53:16,240 [    INFO] s3tester.core.engine: ✅ bucket-policy-permissions-test > DeleteObject (pass) [0.00s] (engine.py:346)
2025-09-08 22:53:16,240 [    INFO] s3tester.core.engine: Executing operation PutObject sequentially... (engine.py:232)
2025-09-08 22:53:16,240 [    INFO] s3tester.operations.PutObject: Starting PutObject (logging_config.py:162)
2025-09-08 22:53:16,251 [    INFO] s3tester.operations.PutObject: PutObject completed successfully in 0.01s (logging_config.py:175)
2025-09-08 22:53:16,251 [    INFO] s3tester.core.engine: ✅ bucket-policy-permissions-test > PutObject (pass) [0.01s] (engine.py:346)
2025-09-08 22:53:16,251 [    INFO] s3tester.core.engine: Phase test completed with 4/4 successful operations (engine.py:264)
2025-09-08 22:53:16,251 [    INFO] s3tester.core.engine.bucket-policy-permissions-test: Executing 4 after-test operations (engine.py:190)
2025-09-08 22:53:16,251 [    INFO] s3tester.core.engine: Executing operation DeleteObject sequentially... (engine.py:232)
2025-09-08 22:53:16,252 [    INFO] s3tester.operations.DeleteObject: Starting DeleteObject (logging_config.py:162)
2025-09-08 22:53:16,265 [    INFO] s3tester.operations.DeleteObject: DeleteObject completed successfully in 0.01s (logging_config.py:175)
2025-09-08 22:53:16,265 [    INFO] s3tester.core.engine: ✅ bucket-policy-permissions-test > DeleteObject (pass) [0.01s] (engine.py:346)
2025-09-08 22:53:16,265 [    INFO] s3tester.core.engine: Executing operation DeleteObject sequentially... (engine.py:232)
2025-09-08 22:53:16,265 [    INFO] s3tester.operations.DeleteObject: Starting DeleteObject (logging_config.py:162)
2025-09-08 22:53:16,277 [    INFO] s3tester.operations.DeleteObject: DeleteObject completed successfully in 0.01s (logging_config.py:175)
2025-09-08 22:53:16,277 [    INFO] s3tester.core.engine: ✅ bucket-policy-permissions-test > DeleteObject (pass) [0.01s] (engine.py:346)
2025-09-08 22:53:16,277 [    INFO] s3tester.core.engine: Executing operation DeleteBucketPolicy sequentially... (engine.py:232)
2025-09-08 22:53:16,277 [    INFO] s3tester.operations.DeleteBucketPolicy: Starting DeleteBucketPolicy (logging_config.py:162)
2025-09-08 22:53:16,294 [    INFO] s3tester.operations.DeleteBucketPolicy: DeleteBucketPolicy completed successfully in 0.02s (logging_config.py:175)
2025-09-08 22:53:16,294 [    INFO] s3tester.core.engine: ✅ bucket-policy-permissions-test > DeleteBucketPolicy (pass) [0.02s] (engine.py:346)
2025-09-08 22:53:16,294 [    INFO] s3tester.core.engine: Executing operation DeleteBucket sequentially... (engine.py:232)
2025-09-08 22:53:16,294 [    INFO] s3tester.operations.DeleteBucket: Starting DeleteBucket (logging_config.py:162)
2025-09-08 22:53:16,304 [    INFO] s3tester.operations.DeleteBucket: DeleteBucket completed successfully in 0.01s (logging_config.py:175)
2025-09-08 22:53:16,304 [    INFO] s3tester.core.engine: ✅ bucket-policy-permissions-test > DeleteBucket (pass) [0.01s] (engine.py:346)
2025-09-08 22:53:16,304 [    INFO] s3tester.core.engine: Phase after completed with 4/4 successful operations (engine.py:264)
2025-09-08 22:53:16,304 [    INFO] s3tester.core.engine.bucket-policy-permissions-test: Test group completed in 5.83s (engine.py:194)
2025-09-08 22:53:16,304 [    INFO] s3tester.core.engine: Test session completed: 11 passed, 0 failed, 0 errors (engine.py:108)
Test Session: 4b44c56e-a74c-461e-9e17-c969dd371f12
Started: 2025-09-08 13:53:10.473205
Finished: 2025-09-08 13:53:16.304572
Duration: 5.83 seconds
Summary:
--------------------------------------------------------------------------------
Total: 11
Passed: 11
Failed: 0
Error: 0
--------------------------------------------------------------------------------

Group: bucket-policy-permissions-test
================================================================================
Operation            Status     Duration   Error
--------------------------------------------------------------------------------
CreateBucket         pass       0.02s
================================================================================

Group: bucket-policy-permissions-test
================================================================================
Operation            Status     Duration   Error
--------------------------------------------------------------------------------
PutObject            pass       0.01s
================================================================================

Group: bucket-policy-permissions-test
================================================================================
Operation            Status     Duration   Error
--------------------------------------------------------------------------------
PutBucketPolicy      pass       0.02s
================================================================================

Group: bucket-policy-permissions-test
================================================================================
Operation            Status     Duration   Error
--------------------------------------------------------------------------------
GetObject            pass       0.01s
================================================================================

Group: bucket-policy-permissions-test
================================================================================
Operation            Status     Duration   Error
--------------------------------------------------------------------------------
PutObject            pass       0.00s Access Denied.
================================================================================

Group: bucket-policy-permissions-test
================================================================================
Operation            Status     Duration   Error
--------------------------------------------------------------------------------
DeleteObject         pass       0.00s Access Denied.
================================================================================

Group: bucket-policy-permissions-test
================================================================================
Operation            Status     Duration   Error
--------------------------------------------------------------------------------
PutObject            pass       0.01s
================================================================================

Group: bucket-policy-permissions-test
================================================================================
Operation            Status     Duration   Error
--------------------------------------------------------------------------------
DeleteObject         pass       0.01s
================================================================================

Group: bucket-policy-permissions-test
================================================================================
Operation            Status     Duration   Error
--------------------------------------------------------------------------------
DeleteObject         pass       0.01s
================================================================================

Group: bucket-policy-permissions-test
================================================================================
Operation            Status     Duration   Error
--------------------------------------------------------------------------------
DeleteBucketPolicy   pass       0.02s
================================================================================

Group: bucket-policy-permissions-test
================================================================================
Operation            Status     Duration   Error
--------------------------------------------------------------------------------
DeleteBucket         pass       0.01s
================================================================================
```

# 후기
* 체감상 간단한 프로토타입을 개발하기에는 충분하지만 유지보수가 필요한 대형 프로젝트에 적용하기에는 문제가 많아보임. (내가 못하는 것일 수도 있음)
* LLM은 생각보다 똑똑하지만 생각보다 멍청함.
	* 단일 작업에 대해서는 충분한 성능을 발휘하지만, 여러 작업을 수행하기 위한 파이프라인을 구축하기 위해서는 좀 더 많은 노력이 필요함.
* 명확한 테스트 환경 구성 필요
	* AI가 스스로 작업을 완료하였다고 말하더라도, 실제로는 완료되지 않았을 수 있음.
	* 이를 구별하기 위한 명확한 테스트 환경이 필수적임.
* 요청을 상세히 작성하는 것도 생각보다 많은 노력이 필요함.
	* 스스로의 니즈를 언어화하는 것이 생각보다 난이도가 높음
* 계속 반복하는게 중요
	* 다른 바이브 코딩 후기를 보면 모두 지속적인 반복을 통해 코드 퀄리티를 올리는 것으로 확인됨.
* 프롬프트와 템플릿등을 활용하여 input을 구조화하는 것이 중요해보임.
	* LLM은 정형화된 데이터를 잘 이해하기 때문에 input을 잘 구조화하는 것이 중요해보임.

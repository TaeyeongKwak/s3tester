# Tasks: S3 API Compatibility Testing Tool (s3tester)

**Input**: Design documents from `/mnt/c/Users/tygwak/project/s3tester/specs/002-aws-s3-api/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, data-model-implementation.md, operations-implementation.md, core-engine-implementation.md, cli-implementation.md, testing-patterns.md, integration-architecture.md

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
   → Tech stack: Python 3.11+, boto3, click, pydantic, pytest
   → Structure: Single project (src/s3tester/, tests/)
2. Load optional design documents ✓:
   → data-model.md: 8 core entities → model tasks
   → contracts/: CLI contract + config schema → contract test tasks
   → quickstart.md: Basic usage scenarios → integration test tasks
3. Generate tasks by category ✓:
   → Setup: Python project, dependencies, linting
   → Tests: CLI contract, config schema, integration scenarios
   → Core: Pydantic models, S3 operations, execution engine
   → Integration: CLI commands, error handling, output formatting
   → Polish: unit tests, performance optimization, documentation
4. Apply task rules ✓:
   → Different files = [P] for parallel execution
   → Tests before implementation (TDD mandatory)
   → Models before services before CLI
5. Number tasks sequentially (T001-T042)
6. Dependencies validated for correct ordering
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- All file paths are absolute and specific

## Phase 3.1: Setup
- [X] **T001** Create Python project structure: `src/s3tester/`, `tests/contract/`, `tests/integration/`, `tests/unit/`, `examples/`
- [X] **T002** Initialize Python project with pyproject.toml: dependencies boto3>=1.40.23, click>=8.1.0, pydantic>=2.5.0, pyyaml>=6.0.1, rich>=13.0.0, jsonschema>=4.25.1
- [X] **T003** [P] Configure development tools: black, mypy, pytest, pre-commit hooks in pyproject.toml

## Phase 3.2: Contract Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### CLI Contract Tests
- [X] **T004** [P] Contract test CLI help and version commands in `tests/contract/test_cli_help.py` - validate help text, version display, exit codes
- [X] **T005** [P] Contract test CLI run command structure in `tests/contract/test_cli_run.py` - validate options (--parallel, --group, --output, --timeout), exit codes 0/1/2/3  
- [X] **T006** [P] Contract test CLI validate command in `tests/contract/test_cli_validate.py` - validate --strict option, configuration validation, exit codes
- [X] **T007** [P] Contract test CLI list command in `tests/contract/test_cli_list.py` - validate list groups/operations/credentials functionality
- [X] **T008** [P] Contract test output formats in `tests/contract/test_output_formats.py` - validate JSON, YAML, table output structure and schema

### Configuration Schema Tests
- [X] **T009** [P] Contract test config schema validation in `tests/contract/test_config_schema.py` - validate YAML structure, required fields, credential uniqueness, operation validation
- [X] **T010** [P] Contract test file path resolution in `tests/contract/test_file_paths.py` - validate file:// prefix handling, relative path resolution, file existence checks

### Integration Scenario Tests  
- [X] **T011** [P] Integration test basic bucket operations in `tests/integration/test_basic_operations.py` - CreateBucket → HeadBucket → ListBuckets → DeleteBucket workflow using moto
- [X] **T012** [P] Integration test file upload workflow in `tests/integration/test_file_upload.py` - CreateBucket → PutObject with file:// → GetObject → DeleteObject → DeleteBucket using moto
- [X] **T013** [P] Integration test permission testing in `tests/integration/test_permissions.py` - multiple credentials, expected access denied scenarios using moto
- [X] **T014** [P] Integration test parallel execution in `tests/integration/test_parallel_execution.py` - concurrent operations, proper result aggregation using moto

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models (Based on data-model-implementation.md)
- [X] **T015** [P] Implement TestConfiguration model in `src/s3tester/config/models.py` - Pydantic model with include processing, validation, load_from_file method
- [X] **T016** [P] Implement GlobalConfig and CredentialSet models in `src/s3tester/config/models.py` - URL validation, region validation, boto3 credential conversion
- [X] **T017** [P] Implement TestGroup and Operation models in `src/s3tester/config/models.py` - state machine, operation validation, parameter handling
- [X] **T018** [P] Implement TestResult and TestSession models in `src/s3tester/config/models.py` - result comparison, session management, summary generation
- [X] **T019** [P] Implement FileReference model in `src/s3tester/config/models.py` - file:// URL parsing, path resolution, content reading

### S3 Operations (Based on operations-implementation.md)
- [X] **T020** [P] Implement operation base classes in `src/s3tester/operations/base.py` - S3Operation ABC, OperationContext, OperationResult, error handling
- [X] **T021** [P] Implement parameter transformers in `src/s3tester/operations/parameters.py` - file reference resolution, bucket name validation, tagging transformation  
- [X] **T022** [P] Implement bucket operations in `src/s3tester/operations/bucket.py` - CreateBucket, DeleteBucket, ListBuckets, HeadBucket operations
- [X] **T023** [P] Implement object operations in `src/s3tester/operations/object.py` - PutObject, GetObject, DeleteObject, HeadObject operations with file handling
- [X] **T024** [P] Implement multipart operations in `src/s3tester/operations/multipart.py` - CreateMultipartUpload, UploadPart, CompleteMultipartUpload operations
- [X] **T025** [P] Implement operation registry in `src/s3tester/operations/registry.py` - OperationRegistry, operation factory, 50+ operation registration
- [X] **T026** [P] Implement retry logic in `src/s3tester/operations/retry.py` - exponential backoff, error classification, retryable vs non-retryable errors

### Core Engine (Based on core-engine-implementation.md)  
- [X] **T027** Implement S3 client factory in `src/s3tester/core/client_factory.py` - boto3 client creation, session management, credential handling, connection testing
- [X] **T028** Implement result collector in `src/s3tester/core/result_collector.py` - group aggregation, failure reporting, performance statistics
- [X] **T029** Implement configuration validator in `src/s3tester/core/validator.py` - comprehensive validation, credential references, file existence, S3 connectivity
- [X] **T030** Implement progress tracker in `src/s3tester/core/progress.py` - Rich progress display, operation tracking, group progress management
- [X] **T031** Implement test execution engine in `src/s3tester/core/engine.py` - async orchestration, ThreadPoolExecutor, before/test/after phases, parallel/sequential modes

## Phase 3.4: CLI Integration (Based on cli-implementation.md)
- [X] **T032** Implement output formatters in `src/s3tester/reporting/formatters.py` - JSON, YAML, table formatters, Rich console display, session formatting
- [X] **T033** Implement CLI commands in `src/s3tester/cli.py` - Click-based commands (run, validate, list), option handling, environment variables, exit codes
- [X] **T034** Implement configuration loader integration in `src/s3tester/cli/config_loader.py` - path resolution, error handling, validation integration
- [X] **T035** Create main entry point in `src/s3tester/__main__.py` - main() function, exception handling, signal handling

## Phase 3.5: Integration Architecture (Based on integration-architecture.md)
- [X] **T036** Implement integration interfaces in `src/s3tester/interfaces.py` - ABC definitions for major components, protocol contracts
- [X] **T037** Implement integration facade in `src/s3tester/integration/facade.py` - S3TesterFacade, complete workflow orchestration, service integration
- [X] **T038** Implement error handling patterns in `src/s3tester/integration/error_handling.py` - ErrorHandler, ErrorContext, exception wrapping and logging

## Phase 3.6: Polish and Validation
- [ ] **T039** [P] Unit tests for data models in `tests/unit/test_models.py` - individual model validation, edge cases, serialization
- [ ] **T040** [P] Unit tests for operations in `tests/unit/test_operations.py` - parameter validation, error handling, retry logic
- [ ] **T041** [P] Performance tests in `tests/integration/test_performance.py` - concurrent operations, memory usage, throughput validation (>10 ops/sec, <10s for 50 operations)
- [ ] **T042** [P] Create example configurations in `examples/` - basic-config.yaml, advanced-config.yaml, permission-test-config.yaml

## Dependencies

### Critical TDD Dependencies (MUST be respected)
- **Tests First**: T004-T014 MUST complete and FAIL before T015-T038
- **Models Before Services**: T015-T019 before T020-T031  
- **Operations Before Engine**: T020-T026 before T031
- **Core Before CLI**: T015-T031 before T032-T035
- **Integration Last**: T036-T038 after core components

### Specific Blocking Dependencies
- T015 (TestConfiguration) blocks T029 (validator), T031 (engine)
- T020 (operation base) blocks T021-T026 (all operations)
- T025 (registry) blocks T031 (engine)
- T031 (engine) blocks T032 (formatters), T033 (CLI)
- T032 (formatters) blocks T033 (CLI commands)

## Parallel Execution Examples

### Phase 3.2 - All Contract Tests (Run Together)
```bash
# Launch T004-T014 together - all independent test files:
Task: "Contract test CLI help/version in tests/contract/test_cli_help.py"
Task: "Contract test CLI run command in tests/contract/test_cli_run.py"  
Task: "Contract test CLI validate in tests/contract/test_cli_validate.py"
Task: "Contract test CLI list in tests/contract/test_cli_list.py"
Task: "Contract test output formats in tests/contract/test_output_formats.py"
Task: "Contract test config schema in tests/contract/test_config_schema.py"
Task: "Contract test file paths in tests/contract/test_file_paths.py"
Task: "Integration test basic operations in tests/integration/test_basic_operations.py"
Task: "Integration test file upload in tests/integration/test_file_upload.py"
Task: "Integration test permissions in tests/integration/test_permissions.py"
Task: "Integration test parallel execution in tests/integration/test_parallel_execution.py"
```

### Phase 3.3 - Data Models (Run Together After Tests Fail)
```bash
# Launch T015-T019 together - all modify same file but different sections:
# NOTE: These are marked [P] but all modify src/s3tester/config/models.py
# Execute in sequence to avoid conflicts, or split into separate files
Task: "TestConfiguration model in src/s3tester/config/models.py"
Task: "GlobalConfig/CredentialSet models in src/s3tester/config/models.py"  
Task: "TestGroup/Operation models in src/s3tester/config/models.py"
Task: "TestResult/TestSession models in src/s3tester/config/models.py"
Task: "FileReference model in src/s3tester/config/models.py"
```

### Phase 3.3 - S3 Operations (Run Together)
```bash
# Launch T020-T026 together - all different files:
Task: "Operation base classes in src/s3tester/operations/base.py"
Task: "Parameter transformers in src/s3tester/operations/parameters.py"
Task: "Bucket operations in src/s3tester/operations/bucket.py"
Task: "Object operations in src/s3tester/operations/object.py"  
Task: "Multipart operations in src/s3tester/operations/multipart.py"
Task: "Operation registry in src/s3tester/operations/registry.py"
Task: "Retry logic in src/s3tester/operations/retry.py"
```

## Validation Checklist
*GATE: All items must be checked before task execution*

- [x] All CLI commands have contract tests (T004-T008)
- [x] All config schema elements have tests (T009-T010)  
- [x] All user scenarios have integration tests (T011-T014)
- [x] All data model entities have implementation tasks (T015-T019)
- [x] All S3 operation categories covered (T020-T026)
- [x] Test tasks come before implementation (T004-T014 before T015+)
- [x] Core components before CLI integration (T015-T031 before T032-T035)
- [x] Each task specifies exact file path
- [x] Parallel tasks are truly independent or noted for sequential execution
- [x] TDD cycle enforced: RED (failing tests) → GREEN (implementation) → REFACTOR

## Constitutional Compliance

### TDD Enforcement
- ✅ Contract tests MUST be written first and MUST fail
- ✅ Integration tests MUST be written before implementation  
- ✅ Each implementation task references its corresponding test
- ✅ No implementation task can start until its tests are failing

### Simplicity Maintained
- ✅ Direct framework usage (boto3, click, pydantic) - no wrapper abstractions
- ✅ Single data model in one module structure  
- ✅ No repository patterns - direct boto3 client usage
- ✅ Library architecture with thin CLI wrapper

### Architecture Requirements  
- ✅ Every feature as library (s3tester.core, s3tester.config, etc.)
- ✅ CLI provides --help, --version, --config, --dry-run, --format options
- ✅ Real dependencies in tests (moto for S3 mocking)
- ✅ Structured logging with JSON format
- ✅ Version 0.1.0 with build increments

## Notes
- Execute tests in Phase 3.2 FIRST - they must fail before proceeding
- [P] tasks can run concurrently if in different files
- Tasks T015-T019 modify same file - execute sequentially despite [P] marking  
- Commit after each task completion for TDD tracking
- Use moto library for S3 mocking in all tests
- Follow constitutional requirements: tests before implementation, real dependencies, simple architecture
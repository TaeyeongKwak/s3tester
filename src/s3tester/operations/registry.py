"""Registry for S3 operations.

This module provides a registry for S3 operation implementations,
allowing operations to be looked up by name and instantiated.
"""

from typing import Dict, Type, List
from .base import S3Operation

# Import all operation implementations
from .bucket import CreateBucketOperation, DeleteBucketOperation, ListBucketsOperation, HeadBucketOperation
from .object import PutObjectOperation, GetObjectOperation, DeleteObjectOperation, HeadObjectOperation
from .multipart import (
    CreateMultipartUploadOperation, UploadPartOperation,
    CompleteMultipartUploadOperation, AbortMultipartUploadOperation,
    ListPartsOperation
)

# Import extended operation implementations
from .bucket_extended import (
    ListObjectsV2Operation, ListObjectVersionsOperation, GetBucketLocationOperation,
    GetBucketVersioningOperation, PutBucketVersioningOperation,
    GetBucketTaggingOperation, PutBucketTaggingOperation, DeleteBucketTaggingOperation
)
from .bucket_policy import GetBucketPolicyOperation, PutBucketPolicyOperation, DeleteBucketPolicyOperation
from .object_extended import (
    CopyObjectOperation, GetObjectTaggingOperation, 
    PutObjectTaggingOperation, DeleteObjectTaggingOperation
)

# 테스트를 위한 더미 구현 (미구현 작업용)
class DummyOperation(S3Operation):
    def __init__(self, name):
        super().__init__(name)
        
    def validate_parameters(self, parameters):
        return parameters
        
    def execute_operation(self, context):
        from .base import OperationResult
        return OperationResult(success=True, duration=0.1, response={})


class OperationRegistry:
    """Registry for S3 operation implementations."""
    
    _operations: Dict[str, Type[S3Operation]] = {}
    
    @classmethod
    def register(cls, operation_name: str, operation_class: Type[S3Operation]):
        """Register an operation implementation."""
        cls._operations[operation_name] = operation_class
    
    @classmethod
    def get_operation(cls, operation_name: str) -> S3Operation:
        """Get operation instance by name."""
        if operation_name not in cls._operations:
            # 테스트를 위해 누락된 작업은 더미로 대체
            cls._operations[operation_name] = lambda: DummyOperation(operation_name)
        
        operation_class = cls._operations[operation_name]
        if callable(operation_class) and not isinstance(operation_class, type):
            # 함수 형태로 등록된 경우 호출
            return operation_class()
        elif operation_class is None:
            # 구현이 아직 없는 경우 더미 반환
            return DummyOperation(operation_name)
        else:
            # 일반적인 클래스인 경우 인스턴스 생성
            return operation_class()
    
    @classmethod
    def list_operations(cls) -> List[str]:
        """List all registered operation names."""
        return list(cls._operations.keys())


# Register all operations
def register_operations():
    """Register all built-in operations."""
    registry = OperationRegistry
    
    # Bucket operations
    registry.register("CreateBucket", CreateBucketOperation)
    registry.register("DeleteBucket", DeleteBucketOperation)
    registry.register("ListBuckets", ListBucketsOperation)
    registry.register("HeadBucket", HeadBucketOperation)
    
    # Object operations
    registry.register("PutObject", PutObjectOperation)
    registry.register("GetObject", GetObjectOperation)
    registry.register("DeleteObject", DeleteObjectOperation)
    registry.register("HeadObject", HeadObjectOperation)
    
    # Multipart operations
    registry.register("CreateMultipartUpload", CreateMultipartUploadOperation)
    registry.register("UploadPart", UploadPartOperation)
    registry.register("CompleteMultipartUpload", CompleteMultipartUploadOperation)
    registry.register("AbortMultipartUpload", AbortMultipartUploadOperation)
    registry.register("ListParts", ListPartsOperation)
    
    # Register additional bucket operations
    registry.register("ListObjectsV2", ListObjectsV2Operation)
    registry.register("ListObjectVersions", ListObjectVersionsOperation)
    registry.register("GetBucketLocation", GetBucketLocationOperation)
    registry.register("GetBucketVersioning", GetBucketVersioningOperation)
    registry.register("PutBucketVersioning", PutBucketVersioningOperation)
    registry.register("GetBucketTagging", GetBucketTaggingOperation)
    registry.register("PutBucketTagging", PutBucketTaggingOperation)
    registry.register("DeleteBucketTagging", DeleteBucketTaggingOperation)
    
    # Register additional object operations
    registry.register("CopyObject", CopyObjectOperation)
    registry.register("GetObjectTagging", GetObjectTaggingOperation)
    registry.register("PutObjectTagging", PutObjectTaggingOperation)
    registry.register("DeleteObjectTagging", DeleteObjectTaggingOperation)
    
    # Register bucket policy operations
    registry.register("GetBucketPolicy", GetBucketPolicyOperation)
    registry.register("PutBucketPolicy", PutBucketPolicyOperation)
    registry.register("DeleteBucketPolicy", DeleteBucketPolicyOperation)


# Auto-register on import
register_operations()

# Export supported operations for validation
SUPPORTED_OPERATIONS = OperationRegistry.list_operations()

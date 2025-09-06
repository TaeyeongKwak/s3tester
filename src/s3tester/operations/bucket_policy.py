"""Bucket policy operations for S3 testing.

This module implements S3 bucket policy-related operations including:
- GetBucketPolicy
- PutBucketPolicy
- DeleteBucketPolicy
"""

import json
from typing import Dict, Any
from botocore.exceptions import ClientError
from .base import S3Operation, OperationContext, OperationResult
from .parameters import ParameterTransformer


class GetBucketPolicyOperation(S3Operation):
    """Get the policy for an S3 bucket."""
    
    def __init__(self):
        super().__init__("GetBucketPolicy")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GetBucketPolicy parameters."""
        if 'bucket' not in parameters:
            raise ValueError("GetBucketPolicy requires 'bucket' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        return {'Bucket': bucket}
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute GetBucketPolicy operation."""
        try:
            response = context.s3_client.get_bucket_policy(**context.parameters)
            
            # If the policy exists, it's returned as a string in 'Policy' key
            # We parse it to JSON for easier inspection
            if 'Policy' in response:
                policy_str = response['Policy']
                policy_json = json.loads(policy_str)
                response['PolicyJson'] = policy_json
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"GetBucketPolicy failed: {error_code} - {error_message}")
            
            # NoSuchBucketPolicy is common and not a fatal error
            if error_code == 'NoSuchBucketPolicy':
                return OperationResult(
                    success=True,
                    duration=0.0,
                    response={'PolicyStatus': 'NoPolicy'}
                )
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


class PutBucketPolicyOperation(S3Operation):
    """Set a policy on an S3 bucket."""
    
    def __init__(self):
        super().__init__("PutBucketPolicy")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PutBucketPolicy parameters."""
        if 'bucket' not in parameters:
            raise ValueError("PutBucketPolicy requires 'bucket' parameter")
            
        if 'policy' not in parameters:
            raise ValueError("PutBucketPolicy requires 'policy' parameter")
            
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        policy = parameters['policy']
        
        # Convert policy from dictionary to JSON string if needed
        if isinstance(policy, dict):
            policy_str = json.dumps(policy)
        elif isinstance(policy, str):
            # Verify that the policy string is valid JSON
            try:
                json.loads(policy)
                policy_str = policy
            except json.JSONDecodeError:
                raise ValueError("Policy string must be valid JSON")
        else:
            raise ValueError("Policy must be a dictionary or JSON string")
        
        return {
            'Bucket': bucket,
            'Policy': policy_str
        }
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute PutBucketPolicy operation."""
        try:
            response = context.s3_client.put_bucket_policy(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"PutBucketPolicy failed: {error_code} - {error_message}")
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )


class DeleteBucketPolicyOperation(S3Operation):
    """Delete the policy for an S3 bucket."""
    
    def __init__(self):
        super().__init__("DeleteBucketPolicy")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate DeleteBucketPolicy parameters."""
        if 'bucket' not in parameters:
            raise ValueError("DeleteBucketPolicy requires 'bucket' parameter")
        
        bucket = ParameterTransformer.transform_bucket_name(parameters['bucket'])
        return {'Bucket': bucket}
    
    def execute_operation(self, context: OperationContext) -> OperationResult:
        """Execute DeleteBucketPolicy operation."""
        try:
            response = context.s3_client.delete_bucket_policy(**context.parameters)
            
            return OperationResult(
                success=True,
                duration=0.0,
                response=response
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(f"DeleteBucketPolicy failed: {error_code} - {error_message}")
            
            return OperationResult(
                success=False,
                duration=0.0,
                error_code=error_code,
                error_message=error_message,
                response=e.response
            )

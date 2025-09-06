from typing import List, Dict, Any
from collections import defaultdict
from ..config.models import S3TestResult, S3TestResultStatus, S3TestSummary
import logging

class ResultCollector:
    """Collect and aggregate test results."""
    
    def __init__(self):
        self.logger = logging.getLogger("s3tester.result_collector")
        self.results = []  # 테스트를 위한 결과 저장소
        
    def aggregate_by_group(self, results: List[S3TestResult]) -> Dict[str, Dict[str, Any]]:
        """Aggregate results by test group."""
        group_stats = defaultdict(lambda: {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'error': 0,
            'duration': 0.0,
            'operations': []
        })
        
        for result in results:
            group_name = result.group_name
            stats = group_stats[group_name]
            
            stats['total'] += 1
            stats['duration'] += result.duration
            stats['operations'].append(result)
            
            if result.status == S3TestResultStatus.PASS:
                stats['passed'] += 1
            elif result.status == S3TestResultStatus.FAIL:
                stats['failed'] += 1
            elif result.status == S3TestResultStatus.ERROR:
                stats['error'] += 1
        
        # Calculate success rates
        for group_name, stats in group_stats.items():
            if stats['total'] > 0:
                stats['success_rate'] = stats['passed'] / stats['total']
            else:
                stats['success_rate'] = 0.0
        
        return dict(group_stats)
    
    def get_failed_operations(self, results: List[S3TestResult]) -> List[S3TestResult]:
        """Get list of failed operations for reporting."""
        return [
            result for result in results 
            if result.status in [S3TestResultStatus.FAIL, S3TestResultStatus.ERROR]
        ]
    
    def get_performance_stats(self, results: List[S3TestResult]) -> Dict[str, float]:
        """Calculate performance statistics."""
        if not results:
            return {}
        
        durations = [result.duration for result in results]
        durations.sort()
        
        total_duration = sum(durations)
        count = len(durations)
        
        stats = {
            'total_duration': total_duration,
            'average_duration': total_duration / count,
            'min_duration': durations[0],
            'max_duration': durations[-1],
            'operations_per_second': count / total_duration if total_duration > 0 else 0
        }
        
        # Percentiles
        if count >= 2:
            stats['p50_duration'] = durations[int(count * 0.5)]
            stats['p90_duration'] = durations[int(count * 0.9)]
            stats['p95_duration'] = durations[int(count * 0.95)]
        
        return stats
    
    def generate_failure_report(self, results: List[S3TestResult]) -> str:
        """Generate detailed failure report."""
        failed_results = self.get_failed_operations(results)
        
        if not failed_results:
            return "No failures to report."
        
        report_lines = [f"Failure Report ({len(failed_results)} failures):"]
        report_lines.append("")
        
        for result in failed_results:
            report_lines.append(f"❌ {result.group_name} > {result.operation_name}")
            
            if result.error_message:
                report_lines.append(f"   Error: {result.error_message}")
            
            if result.expected.success and not result.success:
                report_lines.append("   Expected: Success")
                report_lines.append("   Actual: Failure")
            elif not result.expected.success and result.expected.error_code:
                expected_error = result.expected.error_code
                actual_error = result.actual.get('Error', {}).get('Code', 'Unknown') if result.actual else 'Unknown'
                report_lines.append(f"   Expected Error: {expected_error}")
                report_lines.append(f"   Actual Error: {actual_error}")
            
            report_lines.append(f"   Duration: {result.duration:.2f}s")
            report_lines.append("")
        
        return "\n".join(report_lines)
        
    # 단위 테스트를 위한 추가 메서드
    def add_result(self, result: Dict[str, Any]) -> None:
        """Add a result to the collector."""
        self.results.append(result)
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get all collected results."""
        return self.results
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistics from the collected results."""
        if not self.results:
            return {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0
            }
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get('success', False))
        failed = total - successful
        
        success_rate = (successful / total) * 100 if total > 0 else 0.0
        
        # Calculate average duration - safely handle both duration_ms and duration keys
        durations = []
        for r in self.results:
            if 'duration_ms' in r:
                durations.append(r['duration_ms'])
            elif 'duration' in r:
                durations.append(r['duration'] * 1000)  # Convert seconds to ms
        
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate,
            "avg_duration_ms": avg_duration
        }

"""
디버깅 도우미 모듈
"""
import datetime
import json
import functools
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Optional, Callable, Union

# 출력 경로 설정
DEBUG_DIR = Path(__file__).parent / "debug_logs"
os.makedirs(DEBUG_DIR, exist_ok=True)

def log_to_file(obj: Any, name: Optional[str] = None, mode: str = 'w') -> str:
    """객체를 파일에 기록합니다."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if name is None:
        name = timestamp
    else:
        name = f"{name}_{timestamp}"
    
    file_path = DEBUG_DIR / f"{name}.json"
    
    try:
        # 객체를 JSON으로 직렬화하여 파일에 저장
        with open(file_path, mode) as f:
            json.dump(obj, f, default=lambda o: str(o), indent=2)
        return f"기록됨: {file_path}"
    except Exception as e:
        return f"오류: {e}"

def debug_decorator(func: Callable) -> Callable:
    """함수 실행 전후 정보를 로깅하는 데코레이터"""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 호출 정보 기록
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = DEBUG_DIR / f"func_{func.__name__}_{timestamp}.log"
        
        with open(log_file, 'w') as f:
            # 함수 정보
            f.write(f"함수: {func.__name__}\n")
            f.write(f"시간: {datetime.datetime.now()}\n")
            f.write(f"경로: {inspect.getfile(func)}\n")
            f.write(f"인자: {args}, {kwargs}\n\n")
            
            try:
                # 함수 실행
                result = func(*args, **kwargs)
                
                # 결과 기록
                f.write("\n결과 타입: {}\n".format(type(result)))
                try:
                    f.write("결과:\n{}\n".format(json.dumps(result, default=lambda o: str(o), indent=2)))
                except:
                    f.write(f"결과(직렬화 불가): {result}\n")
                
                return result
            except Exception as e:
                # 오류 기록
                f.write(f"\n오류 발생: {e}\n")
                import traceback
                f.write(traceback.format_exc())
                raise
    
    return wrapper

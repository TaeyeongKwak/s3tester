"""
Operation counter module for tracking execution order of operations.
"""

class OperationCounter:
    """Singleton class for counting operations."""
    
    _instance = None
    _counter = 0
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OperationCounter, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_next(cls):
        """Get the next operation index."""
        cls._counter += 1
        return cls._counter
    
    @classmethod
    def reset(cls):
        """Reset the operation counter."""
        cls._counter = 0

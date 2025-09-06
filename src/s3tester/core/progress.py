from typing import Optional, Callable
from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeElapsedColumn
from rich.console import Console
import logging

class S3TestProgressTracker:
    """Track and display test execution progress."""
    
    def __init__(self, console: Optional[Console] = None, show_progress: bool = True):
        self.console = console or Console()
        self.show_progress = show_progress
        self.logger = logging.getLogger("s3tester.progress")
        
        self.progress: Optional[Progress] = None
        self.main_task: Optional[TaskID] = None
        self.group_task: Optional[TaskID] = None
        
    def start_session(self, total_groups: int, total_operations: int):
        """Start tracking session progress."""
        if not self.show_progress:
            return
        
        self.progress = Progress(
            TextColumn("[bold blue]{task.fields[name]}", justify="left"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            TextColumn("{task.completed}/{task.total}"),
            "•",
            TimeElapsedColumn(),
            console=self.console,
            expand=True
        )
        
        self.progress.start()
        
        # Create main progress task
        self.main_task = self.progress.add_task(
            "Overall Progress",
            total=total_operations,
            name="Overall Progress"
        )
        
        self.logger.info(f"Started progress tracking: {total_groups} groups, {total_operations} operations")
    
    def start_group(self, group_name: str, operations_count: int):
        """Start tracking group progress."""
        if not self.progress:
            return
        
        if self.group_task:
            self.progress.remove_task(self.group_task)
        
        self.group_task = self.progress.add_task(
            group_name,
            total=operations_count,
            name=f"Group: {group_name}"
        )
    
    def update_operation(self, operation_name: str, success: bool):
        """Update progress for completed operation."""
        if not self.progress:
            return
        
        # Update main task
        if self.main_task:
            self.progress.update(self.main_task, advance=1)
        
        # Update group task
        if self.group_task:
            self.progress.update(self.group_task, advance=1)
        
        # Log operation result
        status = "✅" if success else "❌"
        self.logger.debug(f"{status} {operation_name}")
    
    def finish_group(self, group_name: str):
        """Finish group progress tracking."""
        if not self.progress or not self.group_task:
            return
        
        self.progress.update(self.group_task, completed=True)
        self.logger.info(f"Completed group: {group_name}")
    
    def finish_session(self):
        """Finish session progress tracking."""
        if not self.progress:
            return
        
        if self.main_task:
            self.progress.update(self.main_task, completed=True)
        
        self.progress.stop()
        self.logger.info("Progress tracking completed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.progress:
            self.progress.stop()

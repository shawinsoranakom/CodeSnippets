def is_healthy(self) -> bool:
        if self.dispatcher_task is None:
            return False
        if self.dispatcher_task.done() and not self.is_shutting_down:
            return False
        if self.task_retention_seconds > 0 and self.cleanup_task is None:
            return False
        if (
            self.task_retention_seconds > 0
            and self.cleanup_task is not None
            and self.cleanup_task.done()
            and not self.is_shutting_down
        ):
            return False
        return self.last_worker_error is None
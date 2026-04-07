def refresh(self):
        """Reload the cached task data from the task store."""
        refreshed_task = self.task.get_backend().get_result(self.id)

        for attr in TASK_REFRESH_ATTRS:
            object.__setattr__(self, attr, getattr(refreshed_task, attr))
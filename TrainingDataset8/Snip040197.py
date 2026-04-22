def _submit_executor_task(self, task):
        """Submit a new task to our mock executor."""
        self._executor_tasks.append(task)
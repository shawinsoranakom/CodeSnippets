def _run_executor_tasks(self):
        """Run all tasks that have been submitted to our mock executor."""
        tasks = self._executor_tasks
        self._executor_tasks = []
        for task in tasks:
            task()
def enqueue(self, task, args, kwargs):
        self.validate_task(task)

        result = TaskResult(
            task=task,
            id=get_random_string(32),
            status=TaskResultStatus.READY,
            enqueued_at=None,
            started_at=None,
            last_attempted_at=None,
            finished_at=None,
            args=args,
            kwargs=kwargs,
            backend=self.alias,
            errors=[],
            worker_ids=[],
        )

        self._store_result(result)

        # Copy the task to prevent mutation issues.
        return deepcopy(result)
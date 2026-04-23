async def wait_for_terminal_state(self, task_id: str) -> AsyncParseTask:
        task = self.tasks.get(task_id)
        if task is None:
            raise TaskWaitAbortedError("Task not found")
        if is_task_terminal(task.status):
            return task

        task_event = self.task_events.get(task_id)
        if task_event is None:
            raise TaskWaitAbortedError("Task wait handle is unavailable")

        event_wait_task = asyncio.create_task(task_event.wait())
        manager_wait_task = asyncio.create_task(self.manager_wakeup.wait())
        done: set[asyncio.Task[Any]] = set()
        pending: set[asyncio.Task[Any]] = set()
        try:
            done, pending = await asyncio.wait(
                {event_wait_task, manager_wait_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
        finally:
            for waiter in pending:
                waiter.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            for waiter in done:
                with suppress(asyncio.CancelledError):
                    waiter.result()

        task = self.tasks.get(task_id)
        if task is None:
            if self.is_shutting_down:
                raise TaskWaitAbortedError("Task manager is shutting down")
            raise TaskWaitAbortedError("Task was removed before completion")
        if is_task_terminal(task.status):
            return task
        if self.is_shutting_down:
            raise TaskWaitAbortedError("Task manager is shutting down")
        raise TaskWaitAbortedError(
            self.last_worker_error or "Task manager became unavailable while waiting"
        )
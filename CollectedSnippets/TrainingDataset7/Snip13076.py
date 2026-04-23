async def aenqueue(self, task, args, kwargs):
        """Queue up a task function (or coroutine) to be executed."""
        return await sync_to_async(self.enqueue, thread_sensitive=True)(
            task=task, args=args, kwargs=kwargs
        )
async def stop(self) -> None:
        """Stop the runtime immediately."""
        if not self._running:
            raise RuntimeError("Runtime is not running.")
        self._running = False
        # Wait for all background tasks to finish.
        final_tasks_results = await asyncio.gather(*self._background_tasks, return_exceptions=True)
        for task_result in final_tasks_results:
            if isinstance(task_result, Exception):
                logger.error("Error in background task", exc_info=task_result)
        # Close the host connection.
        if self._host_connection is not None:
            try:
                await self._host_connection.close()
            except asyncio.CancelledError:
                pass
        # Cancel the read task.
        if self._read_task is not None:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
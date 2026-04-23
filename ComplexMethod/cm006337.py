async def cleanup_job(self, job_id: str) -> None:
        """Clean up and release resources for a specific job.

        The cleanup process includes:
          1. Verifying if the job's queue is registered.
          2. Cancelling the running task (if active) and awaiting its termination.
          3. Clearing all items from the job's queue.
          4. Removing the job's entry from the internal registry.

        Args:
            job_id (str): Unique identifier for the job to be cleaned up.
        """
        if job_id not in self._queues:
            await logger.adebug(f"No queue found for job_id {job_id} during cleanup.")
            return

        await logger.adebug(f"Commencing cleanup for job_id {job_id}")
        main_queue, _event_manager, task, _ = self._queues[job_id]

        # Cancel the associated task if it is still running.
        if task and not task.done():
            await logger.adebug(f"Cancelling active task for job_id {job_id}")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError as exc:
                # Check if this was a user-initiated cancellation (user called task.cancel())
                if task.cancelled():
                    # User-initiated cancellation so we explicitly called task.cancel() above
                    await logger.adebug(f"Task for job_id {job_id} was successfully cancelled.")
                    # Re-raise with user cancellation message code
                    exc.args = ("LANGFLOW_USER_CANCELLED",)
                    raise
                # System-initiated cancellation for other reasons
                await logger.adebug(f"Task for job_id {job_id} was cancelled by system.")
                exc.args = ("LANGFLOW_SYSTEM_CANCELLED",)
                raise
            except Exception as exc:
                await logger.aerror(f"Error in task for job_id {job_id} during cancellation: {exc}")
                raise
        await logger.adebug(f"Task cancellation complete for job_id {job_id}")

        # Clear the queue since we just cancelled the task or it has completed
        items_cleared = 0
        while not main_queue.empty():
            try:
                main_queue.get_nowait()
                items_cleared += 1
            except asyncio.QueueEmpty:
                break

        await logger.adebug(f"Removed {items_cleared} items from queue for job_id {job_id}")
        # Remove the job entry from the registry
        self._queues.pop(job_id, None)
        self._job_owners.pop(job_id, None)
        await logger.adebug(f"Cleanup successful for job_id {job_id}: resources have been released.")
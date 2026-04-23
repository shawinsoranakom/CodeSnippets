async def _cleanup_old_queues(self) -> None:
        """Scan all registered job queues and clean up those with completed, failed or orphaned tasks."""
        current_time = asyncio.get_running_loop().time()

        for job_id in list(self._queues.keys()):
            _, _, task, cleanup_time = self._queues[job_id]

            should_cleanup = False
            cleanup_reason = ""

            # Case 1: Orphaned queue (created but task never started)
            if task is None:
                should_cleanup = True
                cleanup_reason = "Orphaned queue (no task associated)"
            # Case 2: Task has finished (Success, Failure, or Cancellation)
            elif task.done():
                should_cleanup = True
                if task.cancelled():
                    cleanup_reason = "Task cancelled"
                elif task.exception() is not None:
                    # Don't try to log the exception yet as it might be handled elsewhere;
                    # the grace period allows other systems to inspect it if needed.
                    cleanup_reason = "Task failed with exception"
                else:
                    cleanup_reason = "Task completed successfully"

            if should_cleanup:
                if cleanup_time is None:
                    # Mark for cleanup by setting the timestamp
                    self._queues[job_id] = (
                        self._queues[job_id][0],
                        self._queues[job_id][1],
                        self._queues[job_id][2],
                        current_time,
                    )
                    await logger.adebug(f"Job queue for job_id {job_id} marked for cleanup - {cleanup_reason}")
                elif current_time - cleanup_time >= self.CLEANUP_GRACE_PERIOD:
                    # Enough time has passed, perform the actual cleanup
                    await logger.adebug(f"Cleaning up job_id {job_id} after grace period due to: {cleanup_reason}")
                    await self.cleanup_job(job_id)
async def execute_with_status(self, job_id: UUID, run_coro_func, *args, **kwargs):
        """Wrapper that manages job status lifecycle around a coroutine.

        This function:
        1. Updates status to IN_PROGRESS before execution
        2. Executes the wrapped function
        3. Updates status to COMPLETED on success or FAILED on error
        4. Sets finished_timestamp when done

        Args:
            job_id: The job ID
            run_coro_func: The coroutine function to wrap
            *args: Positional arguments to pass to run_coro_func
            **kwargs: Keyword arguments to pass to run_coro_func

        Returns:
            The result from run_coro_func

        Raises:
            Exception: Re-raises any exception from run_coro_func after updating status
        """
        from lfx.log import logger

        await logger.ainfo(f"Starting job execution: job_id={job_id}")

        try:
            # Update to IN_PROGRESS
            await logger.adebug(f"Updating job {job_id} status to IN_PROGRESS")
            await self.update_job_status(job_id, JobStatus.IN_PROGRESS)

            # Execute the wrapped function
            await logger.ainfo(f"Executing job function for job_id={job_id}")
            result = await run_coro_func(*args, **kwargs)

        except AssertionError as e:
            # Handle missing required arguments
            await logger.aerror(f"Job {job_id} failed with AssertionError: {e}")
            await self.update_job_status(job_id, JobStatus.FAILED, finished_timestamp=True)
            raise

        except asyncio.TimeoutError as e:
            # Handle timeout specifically
            await logger.aerror(f"Job {job_id} timed out: {e}")
            await self.update_job_status(job_id, JobStatus.TIMED_OUT, finished_timestamp=True)
            raise

        except asyncio.CancelledError as exc:
            # Check the message code to determine if this was user-initiated or system-initiated
            if exc.args and exc.args[0] == "LANGFLOW_USER_CANCELLED":
                # User-initiated cancellation, update status to CANCELLED
                await logger.awarning(f"Job {job_id} was cancelled by user")
                await self.update_job_status(job_id, JobStatus.CANCELLED, finished_timestamp=True)
            else:
                # System-initiated cancellation - update status to FAILED
                await logger.aerror(f"Job {job_id} was cancelled by system")
                await self.update_job_status(job_id, JobStatus.FAILED, finished_timestamp=True)
            raise

        except Exception as e:
            # Handle any other error
            await logger.aexception(f"Job {job_id} failed with unexpected error: {e}")
            await self.update_job_status(job_id, JobStatus.FAILED, finished_timestamp=True)
            raise
        else:
            # Update to COMPLETED
            await logger.ainfo(f"Job {job_id} completed successfully")
            await self.update_job_status(job_id, JobStatus.COMPLETED, finished_timestamp=True)
            return result
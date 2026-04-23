async def refresh_data(self, first_update: bool = False) -> None:
        """Refresh job data."""
        job_data = await self._supervisor_client.jobs.info()
        job_queue: list[Job] = job_data.jobs.copy()
        new_jobs: dict[UUID, Job] = {}
        changed_jobs: list[Job] = []

        # Rebuild our job cache from new info and compare to find changes
        while job_queue:
            job = job_queue.pop(0)
            job_queue.extend(job.child_jobs)
            job = replace(job, child_jobs=[])

            if job.uuid not in self._jobs or job != self._jobs[job.uuid]:
                changed_jobs.append(job)
                new_jobs[job.uuid] = replace(job, child_jobs=[])

        # For any jobs that disappeared which weren't done, tell subscribers they
        # changed to done. We don't know what else happened to them so leave the
        # rest of their state as is rather then guessing
        changed_jobs.extend(
            [
                replace(job, done=True)
                for uuid, job in self._jobs.items()
                if uuid not in new_jobs and job.done is False
            ]
        )

        # Replace our cache and inform subscribers of all changes
        self._jobs = new_jobs
        for job in changed_jobs:
            self._process_job_change(job)

        # If this is the first update register to receive Supervisor events
        if first_update:
            self._dispatcher_disconnect = async_dispatcher_connect(
                self._hass, EVENT_SUPERVISOR_EVENT, self._supervisor_events_to_jobs
            )
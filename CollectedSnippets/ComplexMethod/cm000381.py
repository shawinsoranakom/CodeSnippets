def get_graph_execution_schedules(
        self, graph_id: str | None = None, user_id: str | None = None
    ) -> list[GraphExecutionJobInfo]:
        jobs: list[JobObj] = self.scheduler.get_jobs(jobstore=Jobstores.EXECUTION.value)
        schedules = []
        for job in jobs:
            logger.debug(
                f"Found job {job.id} with cron schedule {job.trigger} and args {job.kwargs}"
            )
            try:
                job_args = GraphExecutionJobArgs.model_validate(job.kwargs)
            except ValidationError:
                continue
            if (
                job.next_run_time is not None
                and (graph_id is None or job_args.graph_id == graph_id)
                and (user_id is None or job_args.user_id == user_id)
            ):
                schedules.append(GraphExecutionJobInfo.from_db(job_args, job))
        return schedules
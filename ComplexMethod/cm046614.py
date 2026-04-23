def _handle_event(self, job: Job, event: dict) -> None:
        """Apply event -> job state + forward to SSE."""
        et = event.get("type")
        msg = event.get("message") if et == "log" else None

        with self._lock:
            if self._job is None or self._job.job_id != job.job_id:
                return
            if et == EVENT_JOB_STARTED:
                self._job.status = "active"
            if et == EVENT_JOB_COMPLETED:
                self._job.status = "completed"
                self._job.finished_at = time.time()
                self._job.analysis = event.get("analysis")
                self._job.artifact_path = event.get("artifact_path")
                self._job.execution_type = event.get("execution_type")
                self._job.dataset = event.get("dataset")
                self._job.processor_artifacts = event.get("processor_artifacts")
                if self._job.progress.total and self._job.progress.total > 0:
                    self._job.progress.done = self._job.progress.total
                    self._job.progress.percent = 100.0
            if et == EVENT_JOB_ERROR:
                self._job.status = "error"
                self._job.finished_at = time.time()
                self._job.error = event.get("error") or "error"

            if msg:
                upd = parse_log_message(msg)
                if upd:
                    apply_update(self._job, upd)

        self._emit(event)
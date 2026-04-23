def _pump_loop(self) -> None:
        """Background thread: consumes worker events + updates job snapshot."""
        while True:
            snap = self._snapshot()
            if snap is None:
                return
            job, proc, mp_q = snap

            event = self._read_queue_with_timeout(mp_q, timeout_sec = 0.25)
            if event is not None:
                self._handle_event(job, event)
                continue

            if proc.is_alive():
                continue

            for e in self._drain_queue(mp_q):
                self._handle_event(job, e)

            with self._lock:
                if self._job and self._job.status in {
                    "pending",
                    "active",
                    "cancelling",
                }:
                    if self._job.status == "cancelling":
                        self._job.status = "cancelled"
                    else:
                        self._job.status = "error"
                        self._job.error = self._job.error or "process exited"
                    self._job.finished_at = time.time()
                    event_type = (
                        EVENT_JOB_CANCELLED
                        if self._job.status == "cancelled"
                        else EVENT_JOB_ERROR
                    )
                    self._emit(
                        {
                            "type": event_type,
                            "ts": time.time(),
                            "job_id": self._job.job_id,
                        }
                    )
            return
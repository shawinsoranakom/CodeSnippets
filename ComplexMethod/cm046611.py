def start(self, *, recipe: dict, run: dict) -> str:
        """Spawn the job subprocess (one at a time, no cap)."""
        llm_columns = recipe.get("columns") or []
        llm_column_count = 0
        if isinstance(llm_columns, list):
            for column in llm_columns:
                if not isinstance(column, dict):
                    continue
                column_type = str(column.get("column_type") or "").strip().lower()
                if column_type.startswith("llm"):
                    llm_column_count += 1
        if llm_column_count <= 0:
            llm_column_count = 1

        with self._lock:
            if self._proc is not None and self._proc.is_alive():
                raise RuntimeError("job already running")

            job_id = uuid.uuid4().hex
            self._job = Job(job_id = job_id, status = "pending", started_at = time.time())
            self._job.progress_columns_total = llm_column_count
            self._events.clear()
            self._seq = 0

            run_payload = dict(run)
            run_payload["_job_id"] = job_id
            mp_q = _CTX.Queue()
            proc = _CTX.Process(
                target = run_job_process,
                kwargs = {"event_queue": mp_q, "recipe": recipe, "run": run_payload},
                daemon = True,
            )
            proc.start()

            self._mp_q = mp_q
            self._proc = proc
            self._pump_thread = threading.Thread(target = self._pump_loop, daemon = True)
            self._pump_thread.start()

            self._emit(
                {"type": EVENT_JOB_ENQUEUED, "ts": time.time(), "job_id": job_id}
            )
            return job_id
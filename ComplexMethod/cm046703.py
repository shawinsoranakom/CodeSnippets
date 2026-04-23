def _flush_metrics_to_db(self) -> None:
        """Flush buffered metrics to the database and update live progress."""
        if (
            not self._metric_buffer
            or not self.current_job_id
            or not self._db_run_created
        ):
            return
        # Cap buffer to prevent unbounded memory growth
        if len(self._metric_buffer) > 500:
            logger.warning(
                "Metric buffer exceeded 500 entries (%d) — trimming oldest",
                len(self._metric_buffer),
            )
            self._metric_buffer = self._metric_buffer[-500:]
        # Snapshot before insert so metrics arriving during the write are preserved
        batch = list(self._metric_buffer)
        try:
            from storage.studio_db import insert_metrics_batch, update_run_progress

            insert_metrics_batch(self.current_job_id, batch)
            del self._metric_buffer[: len(batch)]
            update_run_progress(
                id = self.current_job_id,
                step = self._progress.step,
                loss = self._progress.loss
                if (
                    self._progress.loss is not None
                    and math.isfinite(self._progress.loss)
                )
                else None,
                duration_seconds = self._progress.elapsed_seconds,
            )
        except Exception:
            # Leave buffer intact for retry on next flush
            logger.warning("Failed to flush metrics to DB", exc_info = True)
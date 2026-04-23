def _update_progress(
        self,
        scanned: int | None = None,
        total: int | None = None,
        created: int | None = None,
        skipped: int | None = None,
    ) -> None:
        """Update progress counters (thread-safe)."""
        callback: ProgressCallback | None = None
        progress: Progress | None = None

        with self._lock:
            if self._progress is None:
                return
            if scanned is not None:
                self._progress.scanned = scanned
            if total is not None:
                self._progress.total = total
            if created is not None:
                self._progress.created = created
            if skipped is not None:
                self._progress.skipped = skipped
            if self._progress_callback:
                callback = self._progress_callback
                progress = Progress(
                    scanned=self._progress.scanned,
                    total=self._progress.total,
                    created=self._progress.created,
                    skipped=self._progress.skipped,
                )

        if callback and progress:
            try:
                callback(progress)
            except Exception:
                pass
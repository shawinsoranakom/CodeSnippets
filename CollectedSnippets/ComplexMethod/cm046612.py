def get_dataset(
        self,
        job_id: str,
        *,
        limit: int,
        offset: int = 0,
    ) -> dict[str, Any] | None:
        """Load dataset page (offset + limit) and include total rows."""
        with self._lock:
            if self._job is None or self._job.job_id != job_id:
                return None
            in_memory_dataset = self._job.dataset
            artifact_path = self._job.artifact_path
            job_status = self._job.status

        if in_memory_dataset is not None:
            total = len(in_memory_dataset)
            rows = in_memory_dataset[offset : offset + limit]
            return {"dataset": rows, "total": total}
        if not artifact_path:
            if job_status in {"completed", "error", "cancelled"}:
                return {"error": "artifact path missing"}
            return None

        try:
            base_dataset_path = Path(artifact_path)
            parquet_dir = base_dataset_path / "parquet-files"
            if not parquet_dir.exists():
                return {"error": f"dataset path missing: {parquet_dir}"}

            return self._load_dataset_page(
                parquet_dir = parquet_dir, limit = limit, offset = offset
            )
        except Exception as exc:
            return {"error": f"dataset load failed: {exc}"}
def _ensure_db_run_created(self) -> None:
        """Create the DB row if it doesn't exist yet. Called outside the lock."""
        if self._db_run_created or not self.current_job_id or not self._db_config:
            return
        try:
            from storage.studio_db import create_run

            dataset_name = self._db_config.get("hf_dataset") or next(
                iter(self._db_config.get("local_datasets") or []), "unknown"
            )
            create_run(
                id = self.current_job_id,
                model_name = self._db_config["model_name"],
                dataset_name = dataset_name,
                config_json = _json.dumps(self._db_config),
                started_at = self._db_started_at
                or datetime.now(timezone.utc).isoformat(),
                total_steps = self._progress.total_steps or None,
            )
            self._db_run_created = True
        except Exception:
            logger.warning(
                "Failed to create DB run record for early failure", exc_info = True
            )
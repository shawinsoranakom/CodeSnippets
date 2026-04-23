def start(self) -> None:
        if self.local_path:
            metadata, valid_records, _ = self.get_log_data_from_local(self.local_path)
        else:
            print(f"Search for test log in s3 bucket: {UTILIZATION_BUCKET}")
            metadata, valid_records, _ = self.get_log_data_from_s3(
                self.info.workflow_run_id,
                self.info.job_id,
                self.info.run_attempt,
                self.artifact_prefix,
            )

        if not metadata:
            print("[Log Model] Failed to process test log, metadata is None")
            return None

        if len(valid_records) == 0:
            print("[Log Model] Failed to process test log, no valid records")
            return None
        segments = self.segment_generator.generate(valid_records)

        db_metadata, db_records = UtilizationDbConverter(
            self.info, metadata, valid_records, segments
        ).convert()

        if len(db_records) > 0:
            print(
                f"[db model] Peek db timeseries \n:{json.dumps(asdict(db_records[0]), indent=4)}"
            )

        if self.dry_run:
            print("[dry-run-mode]: no upload in dry run mode")
            return

        version = f"v_{db_metadata.data_model_version}"
        metadata_collection = "util_metadata"
        ts_collection = "util_timeseries"
        if self.debug_mode:
            metadata_collection = f"debug_{metadata_collection}"
            ts_collection = f"debug_{ts_collection}"

        self._upload_utilization_data_to_s3(
            collection=metadata_collection,
            version=version,
            repo=self.info.repo,
            workflow_run_id=self.info.workflow_run_id,
            workflow_run_attempt=self.info.run_attempt,
            job_id=self.info.job_id,
            file_name="metadata",
            docs=[asdict(db_metadata)],
        )

        self._upload_utilization_data_to_s3(
            collection=ts_collection,
            version=version,
            repo=self.info.repo,
            workflow_run_id=self.info.workflow_run_id,
            workflow_run_attempt=self.info.run_attempt,
            job_id=self.info.job_id,
            file_name="time_series",
            docs=[asdict(record) for record in db_records],
        )
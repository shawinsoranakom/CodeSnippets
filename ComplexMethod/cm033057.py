def _oauth_retrieval_drives(
        self,
        field_type: DriveFileFieldType,
        drive_service: GoogleDriveService,
        drive_ids_to_retrieve: list[str],
        checkpoint: GoogleDriveCheckpoint,
        start: SecondsSinceUnixEpoch | None = None,
        end: SecondsSinceUnixEpoch | None = None,
    ) -> Iterator[RetrievedDriveFile | str]:
        def _yield_from_drive(drive_id: str, drive_start: SecondsSinceUnixEpoch | None) -> Iterator[RetrievedDriveFile | str]:
            yield from add_retrieval_info(
                get_files_in_shared_drive(
                    service=drive_service,
                    drive_id=drive_id,
                    field_type=field_type,
                    max_num_pages=SHARED_DRIVE_PAGES_PER_CHECKPOINT,
                    cache_folders=not bool(drive_start),  # only cache folders for 0 or None
                    update_traversed_ids_func=self._update_traversed_parent_ids,
                    start=drive_start,
                    end=end,
                    page_token=checkpoint.completion_map[self.primary_admin_email].next_page_token,
                ),
                self.primary_admin_email,
                DriveRetrievalStage.SHARED_DRIVE_FILES,
                parent_id=drive_id,
            )

        # If we are resuming from a checkpoint, we need to finish retrieving the files from the last drive we retrieved
        if checkpoint.completion_map[self.primary_admin_email].stage == DriveRetrievalStage.SHARED_DRIVE_FILES:
            drive_id = checkpoint.completion_map[self.primary_admin_email].current_folder_or_drive_id
            if drive_id is None:
                raise ValueError("drive id not set in checkpoint")
            resume_start = checkpoint.completion_map[self.primary_admin_email].completed_until
            for file_or_token in _yield_from_drive(drive_id, resume_start):
                if isinstance(file_or_token, str):
                    checkpoint.completion_map[self.primary_admin_email].next_page_token = file_or_token
                    return  # done with the max num pages, return checkpoint
                yield file_or_token
            checkpoint.completion_map[self.primary_admin_email].next_page_token = None

        for drive_id in drive_ids_to_retrieve:
            if drive_id in self._retrieved_folder_and_drive_ids:
                self.logger.info(f"Skipping drive '{drive_id}' as it has already been retrieved")
                continue
            self.logger.info(f"Getting files in shared drive '{drive_id}' as '{self.primary_admin_email}'")
            for file_or_token in _yield_from_drive(drive_id, start):
                if isinstance(file_or_token, str):
                    checkpoint.completion_map[self.primary_admin_email].next_page_token = file_or_token
                    return  # done with the max num pages, return checkpoint
                yield file_or_token
            checkpoint.completion_map[self.primary_admin_email].next_page_token = None
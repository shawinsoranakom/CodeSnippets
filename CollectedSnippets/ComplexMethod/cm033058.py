def _manage_oauth_retrieval(
        self,
        field_type: DriveFileFieldType,
        checkpoint: GoogleDriveCheckpoint,
        start: SecondsSinceUnixEpoch | None = None,
        end: SecondsSinceUnixEpoch | None = None,
    ) -> Iterator[RetrievedDriveFile]:
        if checkpoint.completion_stage == DriveRetrievalStage.START:
            checkpoint.completion_stage = DriveRetrievalStage.OAUTH_FILES
            checkpoint.completion_map[self.primary_admin_email] = StageCompletion(
                stage=DriveRetrievalStage.START,
                completed_until=0,
                current_folder_or_drive_id=None,
            )

        drive_service = get_drive_service(self.creds, self.primary_admin_email)

        if checkpoint.completion_stage == DriveRetrievalStage.OAUTH_FILES:
            completion = checkpoint.completion_map[self.primary_admin_email]
            all_files_start = start
            # if resuming from a checkpoint
            if completion.stage == DriveRetrievalStage.OAUTH_FILES:
                all_files_start = completion.completed_until

            for file_or_token in self._oauth_retrieval_all_files(
                field_type=field_type,
                drive_service=drive_service,
                start=all_files_start,
                end=end,
                page_token=checkpoint.completion_map[self.primary_admin_email].next_page_token,
            ):
                if isinstance(file_or_token, str):
                    checkpoint.completion_map[self.primary_admin_email].next_page_token = file_or_token
                    return  # done with the max num pages, return checkpoint
                yield file_or_token
            checkpoint.completion_stage = DriveRetrievalStage.DRIVE_IDS
            checkpoint.completion_map[self.primary_admin_email].next_page_token = None
            return  # create a new checkpoint

        all_requested = self.include_files_shared_with_me and self.include_my_drives and self.include_shared_drives
        if all_requested:
            # If all 3 are true, we already yielded from get_all_files_for_oauth
            checkpoint.completion_stage = DriveRetrievalStage.DONE
            return

        sorted_drive_ids, sorted_folder_ids = self._determine_retrieval_ids(checkpoint, DriveRetrievalStage.SHARED_DRIVE_FILES)

        if checkpoint.completion_stage == DriveRetrievalStage.SHARED_DRIVE_FILES:
            for file_or_token in self._oauth_retrieval_drives(
                field_type=field_type,
                drive_service=drive_service,
                drive_ids_to_retrieve=sorted_drive_ids,
                checkpoint=checkpoint,
                start=start,
                end=end,
            ):
                if isinstance(file_or_token, str):
                    checkpoint.completion_map[self.primary_admin_email].next_page_token = file_or_token
                    return  # done with the max num pages, return checkpoint
                yield file_or_token
            checkpoint.completion_stage = DriveRetrievalStage.FOLDER_FILES
            checkpoint.completion_map[self.primary_admin_email].next_page_token = None
            return  # create a new checkpoint

        if checkpoint.completion_stage == DriveRetrievalStage.FOLDER_FILES:
            yield from self._oauth_retrieval_folders(
                field_type=field_type,
                drive_service=drive_service,
                drive_ids_to_retrieve=set(sorted_drive_ids),
                folder_ids_to_retrieve=set(sorted_folder_ids),
                checkpoint=checkpoint,
                start=start,
                end=end,
            )

        checkpoint.completion_stage = DriveRetrievalStage.DONE
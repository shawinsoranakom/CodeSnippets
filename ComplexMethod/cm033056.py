def _manage_service_account_retrieval(
        self,
        field_type: DriveFileFieldType,
        checkpoint: GoogleDriveCheckpoint,
        start: SecondsSinceUnixEpoch | None = None,
        end: SecondsSinceUnixEpoch | None = None,
    ) -> Iterator[RetrievedDriveFile]:
        """
        The current implementation of the service account retrieval does some
        initial setup work using the primary admin email, then runs MAX_DRIVE_WORKERS
        concurrent threads, each of which impersonates a different user and retrieves
        files for that user. Technically, the actual work each thread does is "yield the
        next file retrieved by the user", at which point it returns to the thread pool;
        see parallel_yield for more details.
        """
        if checkpoint.completion_stage == DriveRetrievalStage.START:
            checkpoint.completion_stage = DriveRetrievalStage.USER_EMAILS

        if checkpoint.completion_stage == DriveRetrievalStage.USER_EMAILS:
            all_org_emails: list[str] = self._get_all_user_emails()
            checkpoint.user_emails = all_org_emails
            checkpoint.completion_stage = DriveRetrievalStage.DRIVE_IDS
        else:
            if checkpoint.user_emails is None:
                raise ValueError("user emails not set")
            all_org_emails = checkpoint.user_emails

        sorted_drive_ids, sorted_folder_ids = self._determine_retrieval_ids(checkpoint, DriveRetrievalStage.MY_DRIVE_FILES)

        # Setup initial completion map on first connector run
        for email in all_org_emails:
            # don't overwrite existing completion map on resuming runs
            if email in checkpoint.completion_map:
                continue
            checkpoint.completion_map[email] = StageCompletion(
                stage=DriveRetrievalStage.START,
                completed_until=0,
                processed_drive_ids=set(),
            )

        # we've found all users and drives, now time to actually start
        # fetching stuff
        self.logger.info(f"Found {len(all_org_emails)} users to impersonate")
        self.logger.debug(f"Users: {all_org_emails}")
        self.logger.info(f"Found {len(sorted_drive_ids)} drives to retrieve")
        self.logger.debug(f"Drives: {sorted_drive_ids}")
        self.logger.info(f"Found {len(sorted_folder_ids)} folders to retrieve")
        self.logger.debug(f"Folders: {sorted_folder_ids}")

        drive_id_getter = self.make_drive_id_getter(sorted_drive_ids, checkpoint)

        # only process emails that we haven't already completed retrieval for
        non_completed_org_emails = [user_email for user_email, stage_completion in checkpoint.completion_map.items() if stage_completion.stage != DriveRetrievalStage.DONE]

        self.logger.debug(f"Non-completed users remaining: {len(non_completed_org_emails)}")

        # don't process too many emails before returning a checkpoint. This is
        # to resolve the case where there are a ton of emails that don't have access
        # to the drive APIs. Without this, we could loop through these emails for
        # more than 3 hours, causing a timeout and stalling progress.
        email_batch_takes_us_to_completion = True
        MAX_EMAILS_TO_PROCESS_BEFORE_CHECKPOINTING = MAX_DRIVE_WORKERS
        if len(non_completed_org_emails) > MAX_EMAILS_TO_PROCESS_BEFORE_CHECKPOINTING:
            non_completed_org_emails = non_completed_org_emails[:MAX_EMAILS_TO_PROCESS_BEFORE_CHECKPOINTING]
            email_batch_takes_us_to_completion = False

        user_retrieval_gens = [
            self._impersonate_user_for_retrieval(
                email,
                field_type,
                checkpoint,
                drive_id_getter,
                sorted_folder_ids,
                start,
                end,
            )
            for email in non_completed_org_emails
        ]
        yield from parallel_yield(user_retrieval_gens, max_workers=MAX_DRIVE_WORKERS)

        # if there are more emails to process, don't mark as complete
        if not email_batch_takes_us_to_completion:
            return

        remaining_folders = (set(sorted_drive_ids) | set(sorted_folder_ids)) - self._retrieved_folder_and_drive_ids
        if remaining_folders:
            self.logger.warning(f"Some folders/drives were not retrieved. IDs: {remaining_folders}")
        if any(checkpoint.completion_map[user_email].stage != DriveRetrievalStage.DONE for user_email in all_org_emails):
            self.logger.info("some users did not complete retrieval, returning checkpoint for another run")
            return
        checkpoint.completion_stage = DriveRetrievalStage.DONE
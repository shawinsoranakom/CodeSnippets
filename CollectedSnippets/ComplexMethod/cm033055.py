def _impersonate_user_for_retrieval(
        self,
        user_email: str,
        field_type: DriveFileFieldType,
        checkpoint: GoogleDriveCheckpoint,
        get_new_drive_id: Callable[[str], str | None],
        sorted_filtered_folder_ids: list[str],
        start: SecondsSinceUnixEpoch | None = None,
        end: SecondsSinceUnixEpoch | None = None,
    ) -> Iterator[RetrievedDriveFile]:
        self.logger.info(f"Impersonating user {user_email}")
        curr_stage = checkpoint.completion_map[user_email]
        resuming = True
        if curr_stage.stage == DriveRetrievalStage.START:
            self.logger.info(f"Setting stage to {DriveRetrievalStage.MY_DRIVE_FILES.value}")
            curr_stage.stage = DriveRetrievalStage.MY_DRIVE_FILES
            resuming = False
        drive_service = get_drive_service(self.creds, user_email)

        # validate that the user has access to the drive APIs by performing a simple
        # request and checking for a 401
        try:
            self.logger.debug(f"Getting root folder id for user {user_email}")
            get_root_folder_id(drive_service)
        except HttpError as e:
            if e.status_code == 401:
                # fail gracefully, let the other impersonations continue
                # one user without access shouldn't block the entire connector
                self.logger.warning(f"User '{user_email}' does not have access to the drive APIs.")
                # mark this user as done so we don't try to retrieve anything for them
                # again
                curr_stage.stage = DriveRetrievalStage.DONE
                return
            raise
        except RefreshError as e:
            self.logger.warning(f"User '{user_email}' could not refresh their token. Error: {e}")
            # mark this user as done so we don't try to retrieve anything for them
            # again
            yield RetrievedDriveFile(
                completion_stage=DriveRetrievalStage.DONE,
                drive_file={},
                user_email=user_email,
                error=e,
            )
            curr_stage.stage = DriveRetrievalStage.DONE
            return
        # if we are including my drives, try to get the current user's my
        # drive if any of the following are true:
        # - include_my_drives is true
        # - the current user's email is in the requested emails
        if curr_stage.stage == DriveRetrievalStage.MY_DRIVE_FILES:
            if self.include_my_drives or user_email in self._requested_my_drive_emails:
                self.logger.info(
                    f"Getting all files in my drive as '{user_email}. Resuming: {resuming}. Stage completed until: {curr_stage.completed_until}. Next page token: {curr_stage.next_page_token}"
                )

                for file_or_token in add_retrieval_info(
                    get_all_files_in_my_drive_and_shared(
                        service=drive_service,
                        update_traversed_ids_func=self._update_traversed_parent_ids,
                        field_type=field_type,
                        include_shared_with_me=self.include_files_shared_with_me,
                        max_num_pages=MY_DRIVE_PAGES_PER_CHECKPOINT,
                        start=curr_stage.completed_until if resuming else start,
                        end=end,
                        cache_folders=not bool(curr_stage.completed_until),
                        page_token=curr_stage.next_page_token,
                    ),
                    user_email,
                    DriveRetrievalStage.MY_DRIVE_FILES,
                ):
                    if isinstance(file_or_token, str):
                        self.logger.debug(f"Done with max num pages for user {user_email}")
                        checkpoint.completion_map[user_email].next_page_token = file_or_token
                        return  # done with the max num pages, return checkpoint
                    yield file_or_token

            checkpoint.completion_map[user_email].next_page_token = None
            curr_stage.stage = DriveRetrievalStage.SHARED_DRIVE_FILES
            curr_stage.current_folder_or_drive_id = None
            return  # resume from next stage on the next run

        if curr_stage.stage == DriveRetrievalStage.SHARED_DRIVE_FILES:

            def _yield_from_drive(drive_id: str, drive_start: SecondsSinceUnixEpoch | None) -> Iterator[RetrievedDriveFile | str]:
                yield from add_retrieval_info(
                    get_files_in_shared_drive(
                        service=drive_service,
                        drive_id=drive_id,
                        field_type=field_type,
                        max_num_pages=SHARED_DRIVE_PAGES_PER_CHECKPOINT,
                        update_traversed_ids_func=self._update_traversed_parent_ids,
                        cache_folders=not bool(drive_start),  # only cache folders for 0 or None
                        start=drive_start,
                        end=end,
                        page_token=curr_stage.next_page_token,
                    ),
                    user_email,
                    DriveRetrievalStage.SHARED_DRIVE_FILES,
                    parent_id=drive_id,
                )

            # resume from a checkpoint
            if resuming and (drive_id := curr_stage.current_folder_or_drive_id):
                resume_start = curr_stage.completed_until
                for file_or_token in _yield_from_drive(drive_id, resume_start):
                    if isinstance(file_or_token, str):
                        checkpoint.completion_map[user_email].next_page_token = file_or_token
                        return  # done with the max num pages, return checkpoint
                    yield file_or_token

            drive_id = get_new_drive_id(user_email)
            if drive_id:
                self.logger.info(f"Getting files in shared drive '{drive_id}' as '{user_email}. Resuming: {resuming}")
                curr_stage.completed_until = 0
                curr_stage.current_folder_or_drive_id = drive_id
                for file_or_token in _yield_from_drive(drive_id, start):
                    if isinstance(file_or_token, str):
                        checkpoint.completion_map[user_email].next_page_token = file_or_token
                        return  # done with the max num pages, return checkpoint
                    yield file_or_token
                curr_stage.current_folder_or_drive_id = None
                return  # get a new drive id on the next run

            checkpoint.completion_map[user_email].next_page_token = None
            curr_stage.stage = DriveRetrievalStage.FOLDER_FILES
            curr_stage.current_folder_or_drive_id = None
            return  # resume from next stage on the next run

        # In the folder files section of service account retrieval we take extra care
        # to not retrieve duplicate docs. In particular, we only add a folder to
        # retrieved_folder_and_drive_ids when all users are finished retrieving files
        # from that folder, and maintain a set of all file ids that have been retrieved
        # for each folder. This might get rather large; in practice we assume that the
        # specific folders users choose to index don't have too many files.
        if curr_stage.stage == DriveRetrievalStage.FOLDER_FILES:

            def _yield_from_folder_crawl(folder_id: str, folder_start: SecondsSinceUnixEpoch | None) -> Iterator[RetrievedDriveFile]:
                for retrieved_file in crawl_folders_for_files(
                    service=drive_service,
                    parent_id=folder_id,
                    field_type=field_type,
                    user_email=user_email,
                    traversed_parent_ids=self._retrieved_folder_and_drive_ids,
                    update_traversed_ids_func=self._update_traversed_parent_ids,
                    start=folder_start,
                    end=end,
                ):
                    yield retrieved_file

            # resume from a checkpoint
            last_processed_folder = None
            if resuming:
                folder_id = curr_stage.current_folder_or_drive_id
                if folder_id is None:
                    self.logger.warning(f"folder id not set in checkpoint for user {user_email}. This happens occasionally when the connector is interrupted and resumed.")
                else:
                    resume_start = curr_stage.completed_until
                    yield from _yield_from_folder_crawl(folder_id, resume_start)
                last_processed_folder = folder_id

            skipping_seen_folders = last_processed_folder is not None
            # NOTE: this assumes a small number of folders to crawl. If someone
            # really wants to specify a large number of folders, we should use
            # binary search to find the first unseen folder.
            num_completed_folders = 0
            for folder_id in sorted_filtered_folder_ids:
                if skipping_seen_folders:
                    skipping_seen_folders = folder_id != last_processed_folder
                    continue

                if folder_id in self._retrieved_folder_and_drive_ids:
                    continue

                curr_stage.completed_until = 0
                curr_stage.current_folder_or_drive_id = folder_id

                if num_completed_folders >= FOLDERS_PER_CHECKPOINT:
                    return  # resume from this folder on the next run

                self.logger.info(f"Getting files in folder '{folder_id}' as '{user_email}'")
                yield from _yield_from_folder_crawl(folder_id, start)
                num_completed_folders += 1

        curr_stage.stage = DriveRetrievalStage.DONE
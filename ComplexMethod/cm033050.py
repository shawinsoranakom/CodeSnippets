def crawl_folders_for_files(
    service: Resource,
    parent_id: str,
    field_type: DriveFileFieldType,
    user_email: str,
    traversed_parent_ids: set[str],
    update_traversed_ids_func: Callable[[str], None],
    start: SecondsSinceUnixEpoch | None = None,
    end: SecondsSinceUnixEpoch | None = None,
) -> Iterator[RetrievedDriveFile]:
    """
    This function starts crawling from any folder. It is slower though.
    """
    logging.info("Entered crawl_folders_for_files with parent_id: " + parent_id)
    if parent_id not in traversed_parent_ids:
        logging.info("Parent id not in traversed parent ids, getting files")
        found_files = False
        file = {}
        try:
            for file in _get_files_in_parent(
                service=service,
                parent_id=parent_id,
                field_type=field_type,
                start=start,
                end=end,
            ):
                logging.info(f"Found file: {file['name']}, user email: {user_email}")
                found_files = True
                yield RetrievedDriveFile(
                    drive_file=file,
                    user_email=user_email,
                    parent_id=parent_id,
                    completion_stage=DriveRetrievalStage.FOLDER_FILES,
                )
            # Only mark a folder as done if it was fully traversed without errors
            # This usually indicates that the owner of the folder was impersonated.
            # In cases where this never happens, most likely the folder owner is
            # not part of the Google Workspace in question (or for oauth, the authenticated
            # user doesn't own the folder)
            if found_files:
                update_traversed_ids_func(parent_id)
        except Exception as e:
            if isinstance(e, HttpError) and e.status_code == 403:
                # don't yield an error here because this is expected behavior
                # when a user doesn't have access to a folder
                logging.debug(f"Error getting files in parent {parent_id}: {e}")
            else:
                logging.error(f"Error getting files in parent {parent_id}: {e}")
                yield RetrievedDriveFile(
                    drive_file=file,
                    user_email=user_email,
                    parent_id=parent_id,
                    completion_stage=DriveRetrievalStage.FOLDER_FILES,
                    error=e,
                )
    else:
        logging.info(f"Skipping subfolder files since already traversed: {parent_id}")

    for subfolder in _get_folders_in_parent(
        service=service,
        parent_id=parent_id,
    ):
        logging.info("Fetching all files in subfolder: " + subfolder["name"])
        yield from crawl_folders_for_files(
            service=service,
            parent_id=subfolder["id"],
            field_type=field_type,
            user_email=user_email,
            traversed_parent_ids=traversed_parent_ids,
            update_traversed_ids_func=update_traversed_ids_func,
            start=start,
            end=end,
        )
def get_all_files_for_oauth(
    service: GoogleDriveService,
    include_files_shared_with_me: bool,
    include_my_drives: bool,
    # One of the above 2 should be true
    include_shared_drives: bool,
    field_type: DriveFileFieldType,
    max_num_pages: int,
    start: SecondsSinceUnixEpoch | None = None,
    end: SecondsSinceUnixEpoch | None = None,
    page_token: str | None = None,
) -> Iterator[GoogleDriveFileType | str]:
    kwargs = {ORDER_BY_KEY: GoogleFields.MODIFIED_TIME.value}
    if page_token:
        logging.info(f"Using page token: {page_token}")
        kwargs[PAGE_TOKEN_KEY] = page_token

    should_get_all = include_shared_drives and include_my_drives and include_files_shared_with_me
    corpora = "allDrives" if should_get_all else "user"

    file_query = f"mimeType != '{DRIVE_FOLDER_TYPE}'"
    file_query += " and trashed = false"
    file_query += generate_time_range_filter(start, end)

    if not should_get_all:
        if include_files_shared_with_me and not include_my_drives:
            file_query += " and not 'me' in owners"
        if not include_files_shared_with_me and include_my_drives:
            file_query += " and 'me' in owners"

    yield from execute_paginated_retrieval_with_max_pages(
        max_num_pages=max_num_pages,
        retrieval_function=service.files().list,
        list_key="files",
        continue_on_404_or_403=False,
        corpora=corpora,
        includeItemsFromAllDrives=should_get_all,
        supportsAllDrives=should_get_all,
        fields=_get_fields_for_file_type(field_type),
        q=file_query,
        **kwargs,
    )
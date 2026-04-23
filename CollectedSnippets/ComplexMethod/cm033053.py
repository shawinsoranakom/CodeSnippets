def __init__(
        self,
        include_shared_drives: bool = False,
        include_my_drives: bool = False,
        include_files_shared_with_me: bool = False,
        shared_drive_urls: str | None = None,
        my_drive_emails: str | None = None,
        shared_folder_urls: str | None = None,
        specific_user_emails: str | None = None,
        batch_size: int = INDEX_BATCH_SIZE,
        time_buffer_seconds: int = GOOGLE_DRIVE_SYNC_TIME_BUFFER_SECONDS,
    ) -> None:
        if not any(
            (
                include_shared_drives,
                include_my_drives,
                include_files_shared_with_me,
                shared_folder_urls,
                my_drive_emails,
                shared_drive_urls,
            )
        ):
            raise ConnectorValidationError(
                "Nothing to index. Please specify at least one of the following: include_shared_drives, include_my_drives, include_files_shared_with_me, shared_folder_urls, or my_drive_emails"
            )

        specific_requests_made = False
        if bool(shared_drive_urls) or bool(my_drive_emails) or bool(shared_folder_urls):
            specific_requests_made = True
        self.specific_requests_made = specific_requests_made

        # NOTE: potentially modified in load_credentials if using service account
        self.include_files_shared_with_me = False if specific_requests_made else include_files_shared_with_me
        self.include_my_drives = False if specific_requests_made else include_my_drives
        self.include_shared_drives = False if specific_requests_made else include_shared_drives

        shared_drive_url_list = _extract_str_list_from_comma_str(shared_drive_urls)
        self._requested_shared_drive_ids = set(_extract_ids_from_urls(shared_drive_url_list))

        self._requested_my_drive_emails = set(_extract_str_list_from_comma_str(my_drive_emails))

        shared_folder_url_list = _extract_str_list_from_comma_str(shared_folder_urls)
        self._requested_folder_ids = set(_extract_ids_from_urls(shared_folder_url_list))
        self._specific_user_emails = _extract_str_list_from_comma_str(specific_user_emails)

        self._primary_admin_email: str | None = None

        self._creds: OAuthCredentials | ServiceAccountCredentials | None = None
        self._creds_dict: dict[str, Any] | None = None

        # ids of folders and shared drives that have been traversed
        self._retrieved_folder_and_drive_ids: set[str] = set()

        self.allow_images = False

        self.size_threshold = GOOGLE_DRIVE_CONNECTOR_SIZE_THRESHOLD
        self.time_buffer_seconds = max(0, time_buffer_seconds)

        self.logger = logging.getLogger(self.__class__.__name__)
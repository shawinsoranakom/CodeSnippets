def __init__(
        self,
        jira_base_url: str,
        project_key: str | None = None,
        jql_query: str | None = None,
        batch_size: int = INDEX_BATCH_SIZE,
        include_comments: bool = True,
        include_attachments: bool = False,
        labels_to_skip: Sequence[str] | None = None,
        comment_email_blacklist: Sequence[str] | None = None,
        scoped_token: bool = False,
        attachment_size_limit: int | None = None,
        timezone_offset: float | None = None,
        time_buffer_seconds: int | None = JIRA_SYNC_TIME_BUFFER_SECONDS,
    ) -> None:
        if not jira_base_url:
            raise ConnectorValidationError("Jira base URL must be provided.")

        self.jira_base_url = jira_base_url.rstrip("/")
        self.project_key = project_key
        self.jql_query = jql_query
        self.batch_size = batch_size
        self.include_comments = include_comments
        self.include_attachments = include_attachments
        configured_labels = labels_to_skip or JIRA_CONNECTOR_LABELS_TO_SKIP
        self.labels_to_skip = {label.lower() for label in configured_labels}
        self.comment_email_blacklist = {email.lower() for email in comment_email_blacklist or []}
        self.scoped_token = scoped_token
        self.jira_client: JIRA | None = None

        self.max_ticket_size = JIRA_CONNECTOR_MAX_TICKET_SIZE
        self.attachment_size_limit = attachment_size_limit if attachment_size_limit and attachment_size_limit > 0 else _DEFAULT_ATTACHMENT_SIZE_LIMIT
        self._fields_param = _DEFAULT_FIELDS
        self._slim_fields = _SLIM_FIELDS

        tz_offset_value = float(timezone_offset) if timezone_offset is not None else float(JIRA_TIMEZONE_OFFSET)
        self.timezone_offset = tz_offset_value
        self.timezone = timezone(offset=timedelta(hours=tz_offset_value))
        self._timezone_overridden = timezone_offset is not None
        if time_buffer_seconds is None:
            buffer_value = JIRA_SYNC_TIME_BUFFER_SECONDS
        else:
            try:
                buffer_value = int(time_buffer_seconds)
            except (TypeError, ValueError) as exc:
                raise ConnectorValidationError(
                    f"Invalid time_buffer_seconds value ({time_buffer_seconds!r}); expected an integer."
                ) from exc
        self.time_buffer_seconds = max(0, buffer_value)
def __init__(
        self,
        stream_or_string,
        *,
        using=DEFAULT_DB_ALIAS,
        ignorenonexistent=False,
        **options,
    ):
        super().__init__(stream_or_string, **options)
        self.handle_forward_references = options.pop("handle_forward_references", False)
        self.event_stream = pulldom.parse(self.stream, self._make_parser())
        self.db = using
        self.ignore = ignorenonexistent
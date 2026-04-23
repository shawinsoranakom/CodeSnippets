def __init__(
        self,
        metrics_data: dict[str, Any],
        collected_at: datetime | None = None,
        **kwargs: Any,
    ):
        """Initialize a new telemetry metrics record.

        Args:
            metrics_data: Dictionary containing the collected metrics
            collected_at: Timestamp when metrics were collected (defaults to now)
            **kwargs: Additional keyword arguments for SQLAlchemy
        """
        super().__init__(**kwargs)

        # Set defaults for fields that would normally be set by SQLAlchemy
        now = datetime.now(UTC)
        if not hasattr(self, 'id') or self.id is None:
            self.id = str(uuid.uuid4())
        if not hasattr(self, 'upload_attempts') or self.upload_attempts is None:
            self.upload_attempts = 0
        if not hasattr(self, 'created_at') or self.created_at is None:
            self.created_at = now
        if not hasattr(self, 'updated_at') or self.updated_at is None:
            self.updated_at = now

        self.metrics_data = metrics_data
        if collected_at:
            self.collected_at = collected_at
        elif not hasattr(self, 'collected_at') or self.collected_at is None:
            self.collected_at = now
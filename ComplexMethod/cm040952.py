def __init__(
        self,
        port: int | None = None,
        host: str = "localhost",
        db_path: str | None = None,
    ) -> None:
        """
        Creates a DynamoDB server from the local configuration.

        :param port: optional, the port to start the server on (defaults to a random port)
        :param host: localhost by default
        :param db_path: path to the persistence state files used by the DynamoDB Local process
        """

        port = port or get_free_tcp_port()
        super().__init__(port, host)

        self.db_path = (
            f"{config.dirs.data}/dynamodb" if not db_path and config.dirs.data else db_path
        )

        # With persistence and MANUAL save strategy, we start DDBLocal from a temporary folder than gets copied over
        # the "usual" data directory in the `on_before_state_save` hook (see the provider code for more details).
        if is_persistence_enabled() and config.SNAPSHOT_SAVE_STRATEGY == "MANUAL":
            self.db_path = f"{config.dirs.tmp}/dynamodb"
            LOG.debug(
                "Persistence save strategy set to MANUAL. The DB path is temporarily stored at: %s",
                self.db_path,
            )

        # the DYNAMODB_IN_MEMORY variable takes precedence and will set the DB path to None which forces inMemory=true
        if is_env_true("DYNAMODB_IN_MEMORY"):
            # note: with DYNAMODB_IN_MEMORY we do not support persistence
            self.db_path = None

        if self.db_path:
            self.db_path = os.path.abspath(self.db_path)

        self.heap_size = config.DYNAMODB_HEAP_SIZE
        self.delay_transient_statuses = is_env_true("DYNAMODB_DELAY_TRANSIENT_STATUSES")
        self.optimize_db_before_startup = is_env_true("DYNAMODB_OPTIMIZE_DB_BEFORE_STARTUP")
        self.share_db = is_env_true("DYNAMODB_SHARE_DB")
        self.cors = os.getenv("DYNAMODB_CORS", None)
        self.proxy = AwsRequestProxy(self.url)
def _setup_connection(self) -> None:
        """Ensure database is ready to fly."""
        kwargs: dict[str, Any] = {}
        self._completed_first_database_setup = False

        if self.db_url == SQLITE_URL_PREFIX or ":memory:" in self.db_url:
            kwargs["connect_args"] = {"check_same_thread": False}
            kwargs["poolclass"] = MutexPool
            MutexPool.pool_lock = threading.RLock()
            kwargs["pool_reset_on_return"] = None
        elif self.db_url.startswith(SQLITE_URL_PREFIX):
            kwargs["poolclass"] = RecorderPool
            kwargs["recorder_and_worker_thread_ids"] = (
                self.recorder_and_worker_thread_ids
            )
        elif self.db_url.startswith(
            (
                MARIADB_URL_PREFIX,
                MARIADB_PYMYSQL_URL_PREFIX,
                MYSQLDB_URL_PREFIX,
                MYSQLDB_PYMYSQL_URL_PREFIX,
            )
        ):
            kwargs["connect_args"] = {"charset": "utf8mb4"}
            if self.db_url.startswith((MARIADB_URL_PREFIX, MYSQLDB_URL_PREFIX)):
                # If they have configured MySQLDB but don't have
                # the MySQLDB module installed this will throw
                # an ImportError which we suppress here since
                # sqlalchemy will give them a better error when
                # it tried to import it below.
                with contextlib.suppress(ImportError):
                    kwargs["connect_args"]["conv"] = build_mysqldb_conv()

        # Disable extended logging for non SQLite databases
        if not self.db_url.startswith(SQLITE_URL_PREFIX):
            kwargs["echo"] = False

        if self._using_file_sqlite:
            validate_or_move_away_sqlite_database(self.db_url)

        assert not self.engine
        self.engine = create_engine(self.db_url, **kwargs, future=True)
        self._dialect_name = try_parse_enum(SupportedDialect, self.engine.dialect.name)
        self.__dict__.pop("dialect_name", None)
        sqlalchemy_event.listen(self.engine, "connect", self._setup_recorder_connection)

        migration.pre_migrate_schema(self.engine)
        Base.metadata.create_all(self.engine)
        self._get_session = scoped_session(sessionmaker(bind=self.engine, future=True))
        _LOGGER.debug("Connected to recorder database")
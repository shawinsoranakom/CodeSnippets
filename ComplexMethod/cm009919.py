def __init__(
        self,
        namespace: str,
        *,
        engine: Engine | AsyncEngine | None = None,
        db_url: None | str | URL = None,
        engine_kwargs: dict[str, Any] | None = None,
        async_mode: bool = False,
    ) -> None:
        """Initialize the SQLRecordManager.

        This class serves as a manager persistence layer that uses an SQL
        backend to track upserted records. You should specify either a `db_url`
        to create an engine or provide an existing engine.

        Args:
            namespace: The namespace associated with this record manager.
            engine: An already existing SQL Alchemy engine.
            db_url: A database connection string used to create an SQL Alchemy engine.
            engine_kwargs: Additional keyword arguments to be passed when creating the
                engine.
            async_mode: Whether to create an async engine. Driver should support async
                operations. It only applies if `db_url` is provided.

        Raises:
            ValueError: If both db_url and engine are provided or neither.
            AssertionError: If something unexpected happens during engine configuration.
        """
        super().__init__(namespace=namespace)
        if db_url is None and engine is None:
            msg = "Must specify either db_url or engine"
            raise ValueError(msg)

        if db_url is not None and engine is not None:
            msg = "Must specify either db_url or engine, not both"
            raise ValueError(msg)

        _engine: Engine | AsyncEngine
        if db_url:
            if async_mode:
                _engine = create_async_engine(db_url, **(engine_kwargs or {}))
            else:
                _engine = create_engine(db_url, **(engine_kwargs or {}))
        elif engine:
            _engine = engine

        else:
            msg = "Something went wrong with configuration of engine."
            raise AssertionError(msg)

        _session_factory: sessionmaker[Session] | async_sessionmaker[AsyncSession]
        if isinstance(_engine, AsyncEngine):
            _session_factory = async_sessionmaker(bind=_engine)
        else:
            _session_factory = sessionmaker(bind=_engine)

        self.engine = _engine
        self.dialect = _engine.dialect.name
        self.session_factory = _session_factory
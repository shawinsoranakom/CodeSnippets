async def get_async_db_engine(self) -> AsyncEngine:
        async_engine = self._async_engine
        if async_engine:
            return async_engine
        if self.gcp_db_instance:  # GCP environments
            async_engine = await self._create_async_gcp_engine()
        else:
            url: str | URL
            if self.host:
                try:
                    import asyncpg  # noqa: F401
                except Exception as e:
                    raise RuntimeError(
                        "PostgreSQL driver 'asyncpg' is required for async connections but is not installed."
                    ) from e
                password = self.password.get_secret_value() if self.password else None
                url = URL.create(
                    'postgresql+asyncpg',
                    username=self.user or '',
                    password=password,
                    host=self.host,
                    port=self.port,
                    database=self.name,
                )
            else:
                url = f'sqlite+aiosqlite:///{str(self.persistence_dir)}/openhands.db'

            if self.host:
                async_engine = create_async_engine(
                    url,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_recycle=self.pool_recycle,
                    pool_pre_ping=True,
                )
            else:
                async_engine = create_async_engine(
                    url,
                    poolclass=NullPool,
                    pool_pre_ping=True,
                )
        assert async_engine is not None  # Always assigned in either branch above
        self._async_engine = async_engine
        return async_engine
def get_db_engine(self) -> Engine:
        engine = self._engine
        if engine:
            return engine
        if self.gcp_db_instance:  # GCP environments
            engine = self._create_gcp_engine()
        else:
            url: str | URL
            if self.host:
                try:
                    import pg8000  # noqa: F401
                except Exception as e:
                    raise RuntimeError(
                        "PostgreSQL driver 'pg8000' is required for sync connections but is not installed."
                    ) from e
                password = self.password.get_secret_value() if self.password else None
                url = URL.create(
                    'postgresql+pg8000',
                    username=self.user or '',
                    password=password,
                    host=self.host,
                    port=self.port,
                    database=self.name,
                )
            else:
                url = f'sqlite:///{self.persistence_dir}/openhands.db'
            engine = create_engine(
                url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_recycle=self.pool_recycle,
                pool_pre_ping=True,
            )
        assert engine is not None  # Always assigned in either branch above
        self._engine = engine
        return engine
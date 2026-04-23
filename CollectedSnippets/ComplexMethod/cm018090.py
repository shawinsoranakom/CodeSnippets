def recorder_db_url(
    pytestconfig: pytest.Config,
    hass_fixture_setup: list[bool],
    persistent_database: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[str]:
    """Prepare a default database for tests and return a connection URL."""
    assert not hass_fixture_setup

    db_url = cast(str, pytestconfig.getoption("dburl"))
    drop_existing_db = pytestconfig.getoption("drop_existing_db")

    def drop_db() -> None:
        import sqlalchemy as sa  # noqa: PLC0415
        import sqlalchemy_utils  # noqa: PLC0415

        if db_url.startswith("mysql://"):
            made_url = sa.make_url(db_url)
            db = made_url.database
            engine = sa.create_engine(db_url)
            # Check for any open connections to the database before dropping it
            # to ensure that InnoDB does not deadlock.
            with engine.begin() as connection:
                query = sa.text(
                    "select id FROM information_schema.processlist WHERE db=:db and id != CONNECTION_ID()"
                )
                rows = connection.execute(query, parameters={"db": db}).fetchall()
                if rows:
                    raise RuntimeError(
                        f"Unable to drop database {db} because it is in use by {rows}"
                    )
            engine.dispose()
            sqlalchemy_utils.drop_database(db_url)
        elif db_url.startswith("postgresql://"):
            sqlalchemy_utils.drop_database(db_url)

    if db_url == "sqlite://" and persistent_database:
        tmp_path = tmp_path_factory.mktemp("recorder")
        db_url = "sqlite:///" + str(tmp_path / "pytest.db")
    elif db_url.startswith(("mysql://", "postgresql://")):
        import sqlalchemy_utils  # noqa: PLC0415

        if drop_existing_db and sqlalchemy_utils.database_exists(db_url):
            drop_db()

        if sqlalchemy_utils.database_exists(db_url):
            raise RuntimeError(
                f"Database {db_url} already exists. Use --drop-existing-db "
                "to automatically drop existing database before start of test."
            )

        sqlalchemy_utils.create_database(
            db_url,
            encoding="utf8mb4' COLLATE = 'utf8mb4_unicode_ci"
            if db_url.startswith("mysql://")
            else "utf8",
        )
    yield db_url
    if db_url == "sqlite://" and persistent_database:
        rmtree(tmp_path, ignore_errors=True)
    elif db_url.startswith(("mysql://", "postgresql://")):
        drop_db()
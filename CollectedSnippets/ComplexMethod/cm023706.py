def test_setup_connection_for_dialect_sqlite_zero_commit_interval(
    sqlite_version: str,
) -> None:
    """Test setting up the connection for a sqlite dialect with a zero commit interval."""
    instance_mock = MagicMock(commit_interval=0)
    execute_args = []
    close_mock = MagicMock()

    def execute_mock(statement):
        nonlocal execute_args
        execute_args.append(statement)

    def fetchall_mock():
        nonlocal execute_args
        if execute_args[-1] == "SELECT sqlite_version()":
            return [[sqlite_version]]
        return None

    def _make_cursor_mock(*_):
        return MagicMock(execute=execute_mock, close=close_mock, fetchall=fetchall_mock)

    dbapi_connection = MagicMock(cursor=_make_cursor_mock)

    assert (
        util.setup_connection_for_dialect(
            instance_mock, "sqlite", dbapi_connection, True
        )
        is not None
    )

    assert len(execute_args) == 5
    assert execute_args[0] == "PRAGMA journal_mode=WAL"
    assert execute_args[1] == "SELECT sqlite_version()"
    assert execute_args[2] == "PRAGMA cache_size = -16384"
    assert execute_args[3] == "PRAGMA synchronous=FULL"
    assert execute_args[4] == "PRAGMA foreign_keys=ON"

    execute_args = []
    assert (
        util.setup_connection_for_dialect(
            instance_mock, "sqlite", dbapi_connection, False
        )
        is None
    )

    assert len(execute_args) == 3
    assert execute_args[0] == "PRAGMA cache_size = -16384"
    assert execute_args[1] == "PRAGMA synchronous=FULL"
    assert execute_args[2] == "PRAGMA foreign_keys=ON"
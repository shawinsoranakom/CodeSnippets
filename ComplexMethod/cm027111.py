def setup_connection_for_dialect(
    instance: Recorder,
    dialect_name: str,
    dbapi_connection: DBAPIConnection,
    first_connection: bool,
) -> DatabaseEngine | None:
    """Execute statements needed for dialect connection."""
    version: AwesomeVersion | None = None
    slow_range_in_select = False
    slow_dependent_subquery = False
    if dialect_name == SupportedDialect.SQLITE:
        if first_connection:
            old_isolation = dbapi_connection.isolation_level
            dbapi_connection.isolation_level = None
            execute_on_connection(dbapi_connection, "PRAGMA journal_mode=WAL")
            dbapi_connection.isolation_level = old_isolation
            # WAL mode only needs to be setup once
            # instead of every time we open the sqlite connection
            # as its persistent and isn't free to call every time.
            result = query_on_connection(dbapi_connection, "SELECT sqlite_version()")
            version_string = result[0][0]
            version = _extract_version_from_server_response_or_raise(version_string)

            if version < MIN_VERSION_SQLITE:
                _raise_if_version_unsupported(
                    version or version_string, "SQLite", MIN_VERSION_SQLITE
                )

        # The upper bound on the cache size is approximately 16MiB of memory
        execute_on_connection(dbapi_connection, "PRAGMA cache_size = -16384")

        #
        # Enable FULL synchronous if they have a commit interval of 0
        # or NORMAL if they do not.
        #
        # https://sqlite.org/pragma.html#pragma_synchronous
        # The synchronous=NORMAL setting is a good choice for most applications
        # running in WAL mode.
        #
        synchronous = "NORMAL" if instance.commit_interval else "FULL"
        execute_on_connection(dbapi_connection, f"PRAGMA synchronous={synchronous}")

        # enable support for foreign keys
        execute_on_connection(dbapi_connection, "PRAGMA foreign_keys=ON")

    elif dialect_name == SupportedDialect.MYSQL:
        execute_on_connection(dbapi_connection, "SET session wait_timeout=28800")
        if first_connection:
            result = query_on_connection(dbapi_connection, "SELECT VERSION()")
            version_string = result[0][0]
            version = _extract_version_from_server_response(version_string)

            if "mariadb" in version_string.lower():
                if not version or version < MIN_VERSION_MARIA_DB:
                    _raise_if_version_unsupported(
                        version or version_string, "MariaDB", MIN_VERSION_MARIA_DB
                    )
                if version and (
                    (version < RECOMMENDED_MIN_VERSION_MARIA_DB)
                    or (MARIA_DB_106 <= version < RECOMMENDED_MIN_VERSION_MARIA_DB_106)
                    or (MARIA_DB_107 <= version < RECOMMENDED_MIN_VERSION_MARIA_DB_107)
                    or (MARIA_DB_108 <= version < RECOMMENDED_MIN_VERSION_MARIA_DB_108)
                ):
                    instance.hass.add_job(
                        _async_create_mariadb_range_index_regression_issue,
                        instance.hass,
                        version,
                    )
                slow_range_in_select = bool(
                    not version
                    or version < MARIADB_WITH_FIXED_IN_QUERIES_105
                    or MARIA_DB_106 <= version < MARIADB_WITH_FIXED_IN_QUERIES_106
                    or MARIA_DB_107 <= version < MARIADB_WITH_FIXED_IN_QUERIES_107
                    or MARIA_DB_108 <= version < MARIADB_WITH_FIXED_IN_QUERIES_108
                )
            elif not version or version < MIN_VERSION_MYSQL:
                _raise_if_version_unsupported(
                    version or version_string, "MySQL", MIN_VERSION_MYSQL
                )
            else:
                # MySQL
                # https://github.com/home-assistant/core/issues/137178
                slow_dependent_subquery = True

        # Ensure all times are using UTC to avoid issues with daylight savings
        execute_on_connection(dbapi_connection, "SET time_zone = '+00:00'")
    elif dialect_name == SupportedDialect.POSTGRESQL:
        # PostgreSQL does not support a skip/loose index scan so its
        # also slow for large distinct queries:
        # https://wiki.postgresql.org/wiki/Loose_indexscan
        # https://github.com/home-assistant/core/issues/126084
        # so we set slow_range_in_select to True
        slow_range_in_select = True
        if first_connection:
            # server_version_num was added in 2006
            result = query_on_connection(dbapi_connection, "SHOW server_version")
            version_string = result[0][0]
            version = _extract_version_from_server_response(version_string)
            if not version or version < MIN_VERSION_PGSQL:
                _raise_if_version_unsupported(
                    version or version_string, "PostgreSQL", MIN_VERSION_PGSQL
                )

    else:
        _fail_unsupported_dialect(dialect_name)

    if not first_connection:
        return None

    return DatabaseEngine(
        dialect=SupportedDialect(dialect_name),
        version=version,
        optimizer=DatabaseOptimizer(
            slow_range_in_select=slow_range_in_select,
            slow_dependent_subquery=slow_dependent_subquery,
        ),
        max_bind_vars=DEFAULT_MAX_BIND_VARS,
    )
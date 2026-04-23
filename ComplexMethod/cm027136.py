def cleanup_statistics_timestamp_migration(instance: Recorder) -> bool:
    """Clean up the statistics migration from timestamp to datetime.

    Returns False if there are more rows to update.
    Returns True if all rows have been updated.
    """
    engine = instance.engine
    assert engine is not None
    if engine.dialect.name == SupportedDialect.SQLITE:
        for table in STATISTICS_TABLES:
            with session_scope(session=instance.get_session()) as session:
                session.connection().execute(
                    text(
                        f"update {table} set start = NULL, created = NULL, last_reset = NULL;"  # noqa: S608
                    )
                )
    elif engine.dialect.name == SupportedDialect.MYSQL:
        for table in STATISTICS_TABLES:
            with session_scope(session=instance.get_session()) as session:
                if (
                    session.connection()
                    .execute(
                        text(
                            f"UPDATE {table} set start=NULL, created=NULL, last_reset=NULL where start is not NULL LIMIT 100000;"  # noqa: S608
                        )
                    )
                    .rowcount
                ):
                    # We have more rows to update so return False
                    # to indicate we need to run again
                    return False
    elif engine.dialect.name == SupportedDialect.POSTGRESQL:
        for table in STATISTICS_TABLES:
            with session_scope(session=instance.get_session()) as session:
                if (
                    session.connection()
                    .execute(
                        text(
                            f"UPDATE {table} set start=NULL, created=NULL, last_reset=NULL "  # noqa: S608
                            f"where id in (select id from {table} where start is not NULL LIMIT 100000)"
                        )
                    )
                    .rowcount
                ):
                    # We have more rows to update so return False
                    # to indicate we need to run again
                    return False

    from .migration import _drop_index  # noqa: PLC0415

    for table in STATISTICS_TABLES:
        _drop_index(instance.get_session, table, f"ix_{table}_start")
    # We have no more rows to update so return True
    # to indicate we are done
    return True
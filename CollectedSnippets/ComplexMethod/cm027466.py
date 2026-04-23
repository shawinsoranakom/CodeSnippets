async def async_create_sessionmaker(
    hass: HomeAssistant, db_url: str
) -> tuple[scoped_session | None, bool, bool]:
    """Create a session maker for the given db_url.

    This function gets or creates a SQLAlchemy `scoped_session` for the given
    db_url. It reuses existing connections where possible and handles the special
    case for the default recorder's database to use the correct executor.

    Args:
        hass: The Home Assistant instance.
        db_url: The database URL to connect to.

    Returns:
        A tuple containing the following items:
        - (scoped_session | None): The SQLAlchemy session maker for executing
          queries. This is `None` if a connection to the database could not
          be established.
        - (bool): A flag indicating if the query is against the recorder
          database.
        - (bool): A flag indicating if the dedicated recorder database
          executor should be used.

    """
    try:
        instance = get_instance(hass)
    except KeyError:  # No recorder loaded
        uses_recorder_db = False
    else:
        uses_recorder_db = db_url == instance.db_url
    sessmaker: scoped_session | None
    sql_data = _async_get_or_init_domain_data(hass)
    use_database_executor = False
    if uses_recorder_db and instance.dialect_name == SupportedDialect.SQLITE:
        use_database_executor = True
        assert instance.engine is not None
        sessmaker = scoped_session(sessionmaker(bind=instance.engine, future=True))
    # For other databases we need to create a new engine since
    # we want the connection to use the default timezone and these
    # database engines will use QueuePool as its only sqlite that
    # needs our custom pool. If there is already a session maker
    # for this db_url we can use that so we do not create a new engine
    # for every sensor.
    elif db_url in sql_data.session_makers_by_db_url:
        sessmaker = sql_data.session_makers_by_db_url[db_url]
    elif sessmaker := await hass.async_add_executor_job(
        _validate_and_get_session_maker_for_db_url, db_url
    ):
        sql_data.session_makers_by_db_url[db_url] = sessmaker
    else:
        return (None, uses_recorder_db, use_database_executor)

    return (sessmaker, uses_recorder_db, use_database_executor)
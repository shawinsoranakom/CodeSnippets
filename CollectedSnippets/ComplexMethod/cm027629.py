def session_scope(
    *,
    hass: HomeAssistant | None = None,
    session: Session | None = None,
    exception_filter: Callable[[Exception], bool] | None = None,
    read_only: bool = False,
) -> Generator[Session]:
    """Provide a transactional scope around a series of operations.

    read_only is used to indicate that the session is only used for reading
    data and that no commit is required. It does not prevent the session
    from writing and is not a security measure.
    """
    if session is None and hass is not None:
        session = get_instance(hass).get_session()

    if session is None:
        raise RuntimeError("Session required")

    need_rollback = False
    try:
        yield session
        if not read_only and session.get_transaction():
            need_rollback = True
            session.commit()
    except Exception as err:
        _LOGGER.exception("Error executing query")
        if need_rollback:
            session.rollback()
        if not exception_filter or not exception_filter(err):
            raise
    finally:
        session.close()
def execute_stmt_lambda_element(
    session: Session,
    stmt: StatementLambdaElement,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    yield_per: int = DEFAULT_YIELD_STATES_ROWS,
    orm_rows: bool = True,
) -> Sequence[Row] | Result:
    """Execute a StatementLambdaElement.

    If the time window passed is greater than one day
    the execution method will switch to yield_per to
    reduce memory pressure.

    It is not recommended to pass a time window
    when selecting non-ranged rows (ie selecting
    specific entities) since they are usually faster
    with .all().
    """
    use_all = not start_time or ((end_time or dt_util.utcnow()) - start_time).days <= 1
    for tryno in range(RETRIES):
        try:
            if orm_rows:
                executed = session.execute(stmt)
            else:
                executed = session.connection().execute(stmt)
            if use_all:
                return executed.all()
            return executed.yield_per(yield_per)
        except SQLAlchemyError as err:
            _LOGGER.error("Error executing query: %s", err)
            if tryno == RETRIES - 1:
                raise
            time.sleep(QUERY_RETRY_WAIT)

    # Unreachable
    raise RuntimeError
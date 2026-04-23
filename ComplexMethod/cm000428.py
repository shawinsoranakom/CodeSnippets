def _build_raw_where(
    start: datetime | None,
    end: datetime | None,
    provider: str | None,
    user_id: str | None,
    model: str | None = None,
    block_name: str | None = None,
    tracking_type: str | None = None,
    graph_exec_id: str | None = None,
) -> tuple[str, list]:
    """Build a parameterised WHERE clause for raw SQL queries.

    Mirrors the filter logic of ``_build_prisma_where`` so there is a single
    source of truth for which columns are filtered and how. The first clause
    always restricts to ``cost_usd`` tracking type unless *tracking_type* is
    explicitly provided by the caller.
    """
    params: list = []
    clauses: list[str] = []
    idx = 1

    # Always filter by tracking type — defaults to cost_usd for percentile /
    # bucket queries that only make sense on cost-denominated rows.
    tt = tracking_type if tracking_type is not None else "cost_usd"
    clauses.append(f'"trackingType" = ${idx}')
    params.append(tt)
    idx += 1

    if start is not None:
        clauses.append(f'"createdAt" >= ${idx}::timestamptz')
        params.append(start)
        idx += 1

    if end is not None:
        clauses.append(f'"createdAt" <= ${idx}::timestamptz')
        params.append(end)
        idx += 1

    if provider is not None:
        clauses.append(f'"provider" = ${idx}')
        params.append(provider.lower())
        idx += 1

    if user_id is not None:
        clauses.append(f'"userId" = ${idx}')
        params.append(user_id)
        idx += 1

    if model is not None:
        clauses.append(f'"model" = ${idx}')
        params.append(model)
        idx += 1

    if block_name is not None:
        clauses.append(f'LOWER("blockName") = LOWER(${idx})')
        params.append(block_name)
        idx += 1

    if graph_exec_id is not None:
        clauses.append(f'"graphExecId" = ${idx}')
        params.append(graph_exec_id)
        idx += 1

    return (" AND ".join(clauses), params)
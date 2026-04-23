def _build_where(
    start: datetime | None,
    end: datetime | None,
    provider: str | None,
    user_id: str | None,
    table_alias: str = "",
    model: str | None = None,
    block_name: str | None = None,
    tracking_type: str | None = None,
) -> tuple[str, list[Any]]:
    """Legacy SQL WHERE builder — retained so existing unit tests still pass.

    Only used by tests that verify the SQL-string generation logic. All
    production code uses _build_prisma_where instead.
    """
    prefix = f"{table_alias}." if table_alias else ""
    clauses: list[str] = []
    params: list[Any] = []
    idx = 1

    if start:
        clauses.append(f'{prefix}"createdAt" >= ${idx}::timestamptz')
        params.append(start)
        idx += 1
    if end:
        clauses.append(f'{prefix}"createdAt" <= ${idx}::timestamptz')
        params.append(end)
        idx += 1
    if provider:
        clauses.append(f'{prefix}"provider" = ${idx}')
        params.append(provider.lower())
        idx += 1
    if user_id:
        clauses.append(f'{prefix}"userId" = ${idx}')
        params.append(user_id)
        idx += 1
    if model:
        clauses.append(f'{prefix}"model" = ${idx}')
        params.append(model)
        idx += 1
    if block_name:
        clauses.append(f'LOWER({prefix}"blockName") = LOWER(${idx})')
        params.append(block_name)
        idx += 1
    if tracking_type:
        clauses.append(f'{prefix}"trackingType" = ${idx}')
        params.append(tracking_type)
        idx += 1

    return (" AND ".join(clauses) if clauses else "TRUE", params)
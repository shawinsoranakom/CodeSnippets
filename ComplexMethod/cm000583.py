def _run_in_transaction(
    conn: Any,
    dialect_name: str,
    query: str,
    max_rows: int,
    read_only: bool,
) -> tuple[list[dict[str, Any]], list[str], int, bool]:
    """Execute a query inside an explicit transaction, returning results.

    Returns ``(rows, columns, affected_rows, truncated)`` where *truncated*
    is ``True`` when ``fetchmany`` returned exactly ``max_rows`` rows,
    indicating that additional rows may exist in the result set.
    """
    # MSSQL uses T-SQL "BEGIN TRANSACTION"; others use "BEGIN".
    begin_stmt = "BEGIN TRANSACTION" if dialect_name == "mssql" else "BEGIN"
    conn.execute(text(begin_stmt))
    try:
        result = conn.execute(text(query))
        affected = result.rowcount if not result.returns_rows else -1
        columns = list(result.keys()) if result.returns_rows else []
        rows = result.fetchmany(max_rows) if result.returns_rows else []
        truncated = len(rows) == max_rows
        results = [
            {col: _serialize_value(val) for col, val in zip(columns, row)}
            for row in rows
        ]
    except Exception:
        try:
            conn.execute(text("ROLLBACK"))
        except Exception:
            pass
        raise
    else:
        conn.execute(text("ROLLBACK" if read_only else "COMMIT"))
    return results, columns, affected, truncated
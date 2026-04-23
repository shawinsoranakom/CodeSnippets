def _validate_single_statement(
    query: str,
) -> tuple[str | None, sqlparse.sql.Statement | None]:
    """Validate that the query contains exactly one non-empty SQL statement.

    Returns (error_message, parsed_statement). If error_message is not None,
    the query is invalid and parsed_statement will be None.
    """
    stripped = query.strip().rstrip(";").strip()
    if not stripped:
        return "Query is empty.", None

    # Parse the SQL using sqlparse for proper tokenization
    statements = sqlparse.parse(stripped)

    # Filter out empty statements and comment-only statements
    statements = [
        s
        for s in statements
        if s.tokens
        and str(s).strip()
        and not all(
            t.is_whitespace or t.ttype in sqlparse.tokens.Comment for t in s.flatten()
        )
    ]

    if not statements:
        return "Query is empty.", None

    # Reject multiple statements -- prevents injection via semicolons
    if len(statements) > 1:
        return "Only single statements are allowed.", None

    return None, statements[0]
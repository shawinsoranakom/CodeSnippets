def _has_disallowed_into(stmt: sqlparse.sql.Statement) -> bool:
    """Check if a statement contains a disallowed ``INTO`` clause.

    ``SELECT ... INTO @variable`` is a valid read-only MySQL syntax that stores
    a query result into a session-scoped user variable.  All other forms of
    ``INTO`` are data-modifying or file-writing and must be blocked:

    * ``SELECT ... INTO new_table``  (PostgreSQL / MSSQL – creates a table)
    * ``SELECT ... INTO OUTFILE``    (MySQL – writes to the filesystem)
    * ``SELECT ... INTO DUMPFILE``   (MySQL – writes to the filesystem)
    * ``INSERT INTO ...``            (already blocked by INSERT being in the
      disallowed set, but we reject INTO as well for defense-in-depth)

    Returns ``True`` if the statement contains a disallowed ``INTO``.
    """
    flat = list(stmt.flatten())
    for i, token in enumerate(flat):
        if not (
            token.ttype in (sqlparse.tokens.Keyword,)
            and token.normalized.upper() == "INTO"
        ):
            continue

        # Look at the first non-whitespace token after INTO.
        j = i + 1
        while j < len(flat) and flat[j].ttype is sqlparse.tokens.Text.Whitespace:
            j += 1

        if j >= len(flat):
            # INTO at the very end – malformed, block it.
            return True

        next_token = flat[j]
        # MySQL user variable: either a single Name starting with "@"
        # (e.g. ``@total``) or a bare ``@`` Operator token followed by a Name.
        if next_token.ttype is sqlparse.tokens.Name and next_token.value.startswith(
            "@"
        ):
            continue
        if next_token.ttype is sqlparse.tokens.Operator and next_token.value == "@":
            continue

        # Everything else (table name, OUTFILE, DUMPFILE, etc.) is disallowed.
        return True

    return False
def get_docstring_statement(body: DocstringNode) -> cst.SimpleStatementLine:
    """Extracts the docstring from the body of a node.

    Args:
        body: The body of a node.

    Returns:
        The docstring statement if it exists, None otherwise.
    """
    if isinstance(body, cst.Module):
        body = body.body
    else:
        body = body.body.body

    if not body:
        return

    statement = body[0]
    if not isinstance(statement, cst.SimpleStatementLine):
        return

    expr = statement
    while isinstance(expr, (cst.BaseSuite, cst.SimpleStatementLine)):
        if len(expr.body) == 0:
            return None
        expr = expr.body[0]

    if not isinstance(expr, cst.Expr):
        return None

    val = expr.value
    if not isinstance(val, (cst.SimpleString, cst.ConcatenatedString)):
        return None

    evaluated_value = val.evaluated_value
    if isinstance(evaluated_value, bytes):
        return None

    return statement
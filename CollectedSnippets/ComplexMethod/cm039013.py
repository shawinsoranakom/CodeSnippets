def check_file(filepath: str) -> list[str]:
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
    except (OSError, UnicodeDecodeError):
        return []

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return []

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if isinstance(item.context_expr, ast.BoolOp):
                    op = "and" if isinstance(item.context_expr.op, ast.And) else "or"
                    violations.append(
                        f"{filepath}:{item.context_expr.lineno}: "
                        f"boolean `{op}` used to combine context managers "
                        f"in `with` statement — use a comma instead"
                    )
    return violations
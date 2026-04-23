def _safe_eval_expression(expression: str, local_vars: dict) -> Any:
    """
    Evaluate a computed field expression safely using AST validation.

    Allows simple transforms (math, string methods, attribute access on data)
    while blocking dangerous operations (__import__, dunder access, etc.).

    Args:
        expression: The Python expression string to evaluate.
        local_vars: The local variables (extracted item fields) available to the expression.

    Returns:
        The result of evaluating the expression.

    Raises:
        ValueError: If the expression contains disallowed constructs.
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid expression syntax: {e}")

    for node in ast.walk(tree):
        # Block import statements
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError("Import statements are not allowed in expressions")

        # Block attribute access to dunder attributes (e.g., __class__, __globals__)
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise ValueError(
                f"Access to private/dunder attribute '{node.attr}' is not allowed"
            )

        # Block calls to __import__ or any name starting with _
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id.startswith("_"):
                raise ValueError(
                    f"Calling '{func.id}' is not allowed in expressions"
                )
            if isinstance(func, ast.Attribute) and func.attr.startswith("_"):
                raise ValueError(
                    f"Calling '{func.attr}' is not allowed in expressions"
                )

    safe_globals = {"__builtins__": _SAFE_EVAL_BUILTINS}
    return eval(compile(tree, "<expression>", "eval"), safe_globals, local_vars)
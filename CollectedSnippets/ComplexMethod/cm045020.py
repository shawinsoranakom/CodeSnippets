def _evaluate_simple_expression(expr: str, namespace: dict[str, Any]) -> Any:
    """Evaluate a simple expression against the namespace.

    Supports:
    - Dot-path access: ``steps.specify.output.file``
    - Comparisons: ``==``, ``!=``, ``>``, ``<``, ``>=``, ``<=``
    - Boolean operators: ``and``, ``or``, ``not``
    - ``in``, ``not in``
    - Pipe filters: ``| default('...')``, ``| join(', ')``, ``| contains('...')``, ``| map('...')``
    - String and numeric literals
    """
    expr = expr.strip()

    # String literal — check before pipes and operators so quoted strings
    # containing | or operator keywords are not mis-parsed.
    if (expr.startswith("'") and expr.endswith("'")) or (
        expr.startswith('"') and expr.endswith('"')
    ):
        return expr[1:-1]

    # Handle pipe filters
    if "|" in expr:
        parts = expr.split("|", 1)
        value = _evaluate_simple_expression(parts[0].strip(), namespace)
        filter_expr = parts[1].strip()

        # Parse filter name and argument
        filter_match = re.match(r"(\w+)\((.+)\)", filter_expr)
        if filter_match:
            fname = filter_match.group(1)
            farg = _evaluate_simple_expression(filter_match.group(2).strip(), namespace)
            if fname == "default":
                return _filter_default(value, farg)
            if fname == "join":
                return _filter_join(value, farg)
            if fname == "map":
                return _filter_map(value, farg)
            if fname == "contains":
                return _filter_contains(value, farg)
        # Filter without args
        filter_name = filter_expr.strip()
        if filter_name == "default":
            return _filter_default(value)
        return value

    # Boolean operators — parse 'or' first (lower precedence) so that
    # 'a or b and c' is evaluated as 'a or (b and c)'.
    if " or " in expr:
        parts = expr.split(" or ", 1)
        left = _evaluate_simple_expression(parts[0].strip(), namespace)
        right = _evaluate_simple_expression(parts[1].strip(), namespace)
        return bool(left) or bool(right)

    if " and " in expr:
        parts = expr.split(" and ", 1)
        left = _evaluate_simple_expression(parts[0].strip(), namespace)
        right = _evaluate_simple_expression(parts[1].strip(), namespace)
        return bool(left) and bool(right)

    if expr.startswith("not "):
        inner = _evaluate_simple_expression(expr[4:].strip(), namespace)
        return not bool(inner)

    # Comparison operators (order matters — check multi-char ops first)
    for op in ("!=", "==", ">=", "<=", ">", "<", " not in ", " in "):
        if op in expr:
            parts = expr.split(op, 1)
            left = _evaluate_simple_expression(parts[0].strip(), namespace)
            right = _evaluate_simple_expression(parts[1].strip(), namespace)
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == ">":
                return _safe_compare(left, right, ">")
            if op == "<":
                return _safe_compare(left, right, "<")
            if op == ">=":
                return _safe_compare(left, right, ">=")
            if op == "<=":
                return _safe_compare(left, right, "<=")
            if op == " in ":
                return left in right if right is not None else False
            if op == " not in ":
                return left not in right if right is not None else True

    # Numeric literal
    try:
        if "." in expr:
            return float(expr)
        return int(expr)
    except (ValueError, TypeError):
        pass

    # Boolean literal
    if expr.lower() == "true":
        return True
    if expr.lower() == "false":
        return False

    # Null
    if expr.lower() in ("none", "null"):
        return None

    # List literal (simple)
    if expr.startswith("[") and expr.endswith("]"):
        inner = expr[1:-1].strip()
        if not inner:
            return []
        items = [_evaluate_simple_expression(i.strip(), namespace) for i in inner.split(",")]
        return items

    # Variable reference (dot-path)
    return _resolve_dot_path(namespace, expr)
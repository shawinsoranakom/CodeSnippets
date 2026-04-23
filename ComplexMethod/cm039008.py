def _extract_priorities(body: list, priorities: dict[str, list[str]], prefix: str):
    """Extract priority lists from if/else statement body."""
    for stmt in body:
        if isinstance(stmt, ast.If):
            is_sm100 = _is_sm100_check(stmt.test)
            if_key = f"{prefix}_sm100" if is_sm100 else f"{prefix}_default"
            else_key = f"{prefix}_default" if is_sm100 else f"{prefix}_sm100"

            if backends := _get_backends_from_return(stmt.body):
                priorities[if_key] = backends
            if backends := _get_backends_from_return(stmt.orelse):
                priorities[else_key] = backends

        elif isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.List):
            backends = [e.attr for e in stmt.value.elts if isinstance(e, ast.Attribute)]
            priorities[f"{prefix}_default"] = backends
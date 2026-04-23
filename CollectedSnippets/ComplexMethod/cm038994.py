def _parse_return_list(
    method: ast.FunctionDef | None, handle_multiple_of: bool = False
) -> list[str]:
    """Extract list items from a method's return statement."""
    if method is None:
        return []
    for stmt in ast.walk(method):
        if not isinstance(stmt, ast.Return):
            continue
        if not isinstance(stmt.value, ast.List):
            continue
        sizes = []
        for elt in stmt.value.elts:
            if isinstance(elt, ast.Constant):
                sizes.append(str(elt.value))
            elif (
                handle_multiple_of
                and isinstance(elt, ast.Call)
                and isinstance(elt.func, ast.Name)
                and elt.func.id == "MultipleOf"
                and elt.args
                and isinstance(elt.args[0], ast.Constant)
            ):
                sizes.append(f"%{elt.args[0].value}")
        if sizes:
            return sizes
    return []
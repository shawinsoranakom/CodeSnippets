def _parse_list_class_var(node: ast.ClassDef, var_name: str) -> list[str] | None:
    """Parse a list-type class variable, returning None if not found."""
    for item in node.body:
        if not isinstance(item, ast.AnnAssign):
            continue
        if not isinstance(item.target, ast.Name):
            continue
        if item.target.id != var_name:
            continue
        if not (item.value and isinstance(item.value, ast.List)):
            continue
        result = []
        for elt in item.value.elts:
            if isinstance(elt, ast.Attribute):
                result.append(elt.attr)
            elif isinstance(elt, ast.Constant):
                result.append(str(elt.value))
        return result
    return None
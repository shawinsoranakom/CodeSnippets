def _find_bool_class_var(class_node: ast.ClassDef, var_name: str) -> bool | None:
    """Find a bool class variable in a class definition. Returns None if not found."""
    for item in class_node.body:
        # Check for annotated assignment: attr: bool = True/False
        if (
            isinstance(item, ast.AnnAssign)
            and isinstance(item.target, ast.Name)
            and item.target.id == var_name
            and isinstance(item.value, ast.Constant)
            and isinstance(item.value.value, bool)
        ):
            return item.value.value
        # Check for plain assignment: attr = True/False
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == var_name
                    and isinstance(item.value, ast.Constant)
                    and isinstance(item.value.value, bool)
                ):
                    return item.value.value
    return None
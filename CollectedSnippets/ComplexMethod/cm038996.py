def _find_cc_in_function(tree: ast.AST, func_name: str) -> str | None:
    """Find a compute capability from is_device_capability_family() calls in a function.

    Looks for the pattern: current_platform.is_device_capability_family(N)
    and converts N (e.g. 100) to a CC string (e.g. "10.x").
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != func_name:
            continue
        for n in ast.walk(node):
            if (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "is_device_capability_family"
                and n.args
                and isinstance(n.args[0], ast.Constant)
                and isinstance(n.args[0].value, int)
            ):
                return f"{n.args[0].value // 10}.x"
    return None
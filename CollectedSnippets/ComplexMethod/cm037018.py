def _index_file(filepath: Path) -> dict[str, str]:
    """Extract documented public names from a Python file using AST parsing.

    Only classes and functions with docstrings are included, since
    mkdocstrings won't generate a page for undocumented symbols.
    """
    names: dict[str, str] = {}
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return names

    module = _module_path(filepath)

    for node in ast.iter_child_nodes(tree):
        if (
            # Class definitions (with docstring)
            isinstance(node, ast.ClassDef)
            and not node.name.startswith("_")
            and _has_docstring(node)
        ) or (
            # Function definitions (with docstring, only uppercase/CamelCase)
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and not node.name.startswith("_")
            and node.name[0].isupper()
            and _has_docstring(node)
        ):
            names[node.name] = f"{module}.{node.name}"

    return names
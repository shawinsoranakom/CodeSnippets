def _extract_imports(source: str) -> set[str]:
    """Extract top-level package names from all imports in Python source via AST.

    Walks the entire AST (including function bodies and try/except blocks) so
    that lazy imports inside ``build_model()`` etc. are captured.  Returns only
    the first segment of each dotted import (e.g. ``foo`` from ``import foo.bar``).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        warnings.warn(
            f"Could not parse component source (SyntaxError: {exc}). "
            "Imports from this component will not be included in requirements.",
            stacklevel=2,
        )
        return set()

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                # Relative import - skip (internal to the component)
                continue
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports
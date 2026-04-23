def collect_top_level_symbols(
    tree: ast.Module, source_lines: list[str]
) -> tuple[Set[str], Set[str], list[str], Set[str]]:
    """Collect all top-level symbols from an AST module.

    Returns:
        Tuple of (class_names, function_names, safe_variable_sources, unsafe_variable_names)
        safe_variable_sources contains the actual source code lines for safe variables
    """
    classes: Set[str] = set()
    functions: Set[str] = set()
    safe_variable_sources: list[str] = []
    unsafe_variables: Set[str] = set()

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if not _is_private(node.name):
                classes.add(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not _is_private(node.name):
                functions.add(node.name)
        elif isinstance(node, ast.Assign):
            is_safe = _is_safe_type_alias(node)
            names = []
            for t in node.targets:
                for n in _iter_assigned_names(t):
                    if not _is_private(n):
                        names.append(n)
            if names:
                if is_safe:
                    # Extract the source code for this assignment
                    start_line = node.lineno - 1  # 0-indexed
                    end_line = node.end_lineno if node.end_lineno else node.lineno
                    source = "\n".join(source_lines[start_line:end_line])
                    safe_variable_sources.append(source)
                else:
                    unsafe_variables.update(names)
        elif isinstance(node, ast.AnnAssign) and node.target:
            # Annotated assignments are always stubbed
            for n in _iter_assigned_names(node.target):
                if not _is_private(n):
                    unsafe_variables.add(n)

    return classes, functions, safe_variable_sources, unsafe_variables
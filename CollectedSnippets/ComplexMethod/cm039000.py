def parse_impl_bool_attr(
    tree: ast.AST,
    class_name: str,
    attr_name: str,
    default: bool = False,
    source_file: Path | None = None,
    _visited: set[str] | None = None,
) -> bool:
    """Parse a boolean class attribute from an impl class, following inheritance.

    Walks up the inheritance chain within the same file and across files
    (by resolving imports) to find the attribute value.
    """
    if _visited is None:
        _visited = set()
    if class_name in _visited:
        return default
    _visited.add(class_name)

    class_node = find_class_in_ast(tree, class_name)
    if class_node is None:
        return default

    # Check directly on this class
    value = _find_bool_class_var(class_node, attr_name)
    if value is not None:
        return value

    # Check parent class
    parent_name = _get_parent_class_name(class_node)
    if parent_name:
        # Try parent in same file first
        parent_node = find_class_in_ast(tree, parent_name)
        if parent_node is not None:
            return parse_impl_bool_attr(
                tree, parent_name, attr_name, default, source_file, _visited
            )

        # Try resolving cross-file import
        parent_file = _resolve_import_to_file(tree, parent_name, source_file)
        if parent_file:
            try:
                parent_tree = ast.parse(parent_file.read_text())
                return parse_impl_bool_attr(
                    parent_tree,
                    parent_name,
                    attr_name,
                    default,
                    parent_file,
                    _visited,
                )
            except Exception:
                pass

    return default
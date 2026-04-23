def _resolve_import_to_file(
    tree: ast.AST, class_name: str, source_file: Path | None = None
) -> Path | None:
    """Try to resolve a class name to its source file via imports in the AST.

    Handles both absolute imports (from vllm.foo import Bar) and relative
    imports (from .foo import Bar) when source_file is provided.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        for alias in node.names:
            actual_name = alias.asname or alias.name
            if actual_name != class_name:
                continue
            if not node.module:
                continue

            if node.level and node.level > 0 and source_file:
                # Relative import: resolve from the source file's directory
                base_dir = source_file.parent
                for _ in range(node.level - 1):
                    base_dir = base_dir.parent
                module_path = node.module.replace(".", "/")
                py_file = base_dir / f"{module_path}.py"
            else:
                # Absolute import
                module_path = node.module.replace(".", "/")
                py_file = REPO_ROOT / f"{module_path}.py"

            if py_file.exists():
                return py_file
    return None
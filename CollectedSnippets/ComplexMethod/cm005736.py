def check_deprecated_imports(components_path: Path) -> list[str]:
    """Check for deprecated import patterns in component files.

    Args:
        components_path: Path to the components directory

    Returns:
        List of error messages for deprecated imports found
    """
    deprecated_imports = []

    # Known deprecated import patterns
    deprecated_patterns = [
        ("langchain.embeddings.base", "langchain_core.embeddings"),
        ("langchain.llms.base", "langchain_core.language_models.llms"),
        ("langchain.chat_models.base", "langchain_core.language_models.chat_models"),
        ("langchain.schema", "langchain_core.messages"),
        ("langchain.vectorstores", "langchain_community.vectorstores"),
        ("langchain.document_loaders", "langchain_community.document_loaders"),
        ("langchain.text_splitter", "langchain_text_splitters"),
    ]

    # Walk through all Python files in components
    for py_file in components_path.rglob("*.py"):
        # Skip private modules
        if py_file.name.startswith("_"):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ""

                    # Check against deprecated patterns
                    for deprecated, replacement in deprecated_patterns:
                        if module.startswith(deprecated):
                            relative_path = py_file.relative_to(components_path.parent)
                            deprecated_imports.append(
                                f"{relative_path}:{node.lineno}: "
                                f"Uses deprecated '{deprecated}' - should use '{replacement}'"
                            )

        except Exception as e:  # noqa: BLE001
            # Report parsing errors but continue - we want to check all files
            print(f"Warning: Could not parse {py_file}: {e}", file=sys.stderr)
            continue

    return deprecated_imports
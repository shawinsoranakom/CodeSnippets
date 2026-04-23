def generate_docs_src_versions() -> None:
    """
    Generate Python version-specific files for all .py files in docs_src.
    """
    docs_src_path = Path("docs_src")
    for py_file in sorted(docs_src_path.rglob("*.py")):
        generate_docs_src_versions_for_file(py_file)
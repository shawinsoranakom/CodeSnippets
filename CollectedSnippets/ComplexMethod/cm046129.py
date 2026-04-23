def create_placeholder_markdown(py_filepath: Path, module_path: str, classes: list[str], functions: list[str]) -> Path:
    """Create a minimal Markdown stub used by mkdocstrings."""
    md_filepath = REFERENCE_DIR / py_filepath.relative_to(PACKAGE_DIR).with_suffix(".md")
    exists = md_filepath.exists()

    header_content = ""
    if exists:
        current = md_filepath.read_text()
        if current.startswith("---"):
            parts = current.split("---", 2)
            if len(parts) > 2:
                header_content = f"---{parts[1]}---\n\n"
    if not header_content:
        header_content = "---\ndescription: TODO ADD DESCRIPTION\nkeywords: TODO ADD KEYWORDS\n---\n\n"

    module_path_dots = module_path
    module_path_fs = module_path.replace(".", "/")
    url = f"https://github.com/{GITHUB_REPO}/blob/main/{module_path_fs}.py"
    pretty = url.replace("__init__.py", "\\_\\_init\\_\\_.py")

    title_content = f"# Reference for `{module_path_fs}.py`\n\n" + contribution_admonition(
        pretty, url, kind="success", title="Improvements"
    )

    md_content = ["<br>\n\n"]
    md_content.extend(f"## ::: {module_path_dots}.{cls}\n\n<br><br><hr><br>\n\n" for cls in classes)
    md_content.extend(f"## ::: {module_path_dots}.{func}\n\n<br><br><hr><br>\n\n" for func in functions)
    if md_content[-1:]:
        md_content[-1] = md_content[-1].replace("<hr><br>\n\n", "")

    md_filepath.parent.mkdir(parents=True, exist_ok=True)
    md_filepath.write_text(header_content + title_content + "".join(md_content) + "\n")

    return _relative_to_workspace(md_filepath)
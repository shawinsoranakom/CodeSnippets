def update_docs_includes_py39_to_py310() -> None:
    """
    Update .md files in docs/en/ to replace _py39 includes with _py310 versions.

    For each include line referencing a _py39 file or directory in docs_src, replace
    the _py39 label with _py310.
    """
    include_pattern = re.compile(r"\{[^}]*docs_src/[^}]*_py39[^}]*\.py[^}]*\}")
    count = 0
    for md_file in sorted(en_docs_path.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        if "_py39" not in content:
            continue
        new_content = include_pattern.sub(
            lambda m: m.group(0).replace("_py39", "_py310"), content
        )
        if new_content != content:
            md_file.write_text(new_content, encoding="utf-8")
            count += 1
            logging.info(f"Updated includes in {md_file}")
    print(f"Updated {count} file(s) ✅")
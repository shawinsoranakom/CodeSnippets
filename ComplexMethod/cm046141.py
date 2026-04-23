def build_reference_placeholders(update_nav: bool = True) -> list[str]:
    """Create minimal placeholder reference files (mkdocstrings-style) and optionally update nav."""
    nav_items: list[str] = []
    created = 0
    orphans = set(REFERENCE_DIR.rglob("*.md"))

    for py_filepath in TQDM(list(PACKAGE_DIR.rglob("*.py")), desc="Building reference stubs", unit="file"):
        classes, functions = extract_classes_and_functions(py_filepath)
        if not classes and not functions:
            continue
        module_path = (
            f"{PACKAGE_DIR.name}.{py_filepath.relative_to(PACKAGE_DIR).with_suffix('').as_posix().replace('/', '.')}"
        )
        md_filepath = REFERENCE_DIR / py_filepath.relative_to(PACKAGE_DIR).with_suffix(".md")
        exists = md_filepath.exists()
        orphans.discard(md_filepath)
        md_rel = create_placeholder_markdown(py_filepath, module_path, classes, functions)
        nav_items.append(str(md_rel))
        if not exists:
            created += 1
    for orphan in orphans:
        orphan.unlink()
    if update_nav:
        update_mkdocs_file(create_nav_menu_yaml(nav_items))
    if created:
        LOGGER.info(f"Created {created} new reference stub files")
    return nav_items
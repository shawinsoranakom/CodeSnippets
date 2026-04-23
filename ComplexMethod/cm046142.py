def build_reference_docs(update_nav: bool = False) -> list[str]:
    """Render full docstring-based reference content."""
    _missing_type_warnings.clear()
    nav_items: list[str] = []
    created = 0

    desc = f"Docstrings {GITHUB_REPO or PACKAGE_DIR.name}"
    for py_filepath in TQDM(list(PACKAGE_DIR.rglob("*.py")), desc=desc, unit="file"):
        md_target = REFERENCE_DIR / py_filepath.relative_to(PACKAGE_DIR).with_suffix(".md")
        exists_before = md_target.exists()
        module = parse_module(py_filepath)
        if not module or (not module.classes and not module.functions):
            continue
        md_rel_filepath = create_markdown(module)
        if not exists_before:
            created += 1
        nav_items.append(str(md_rel_filepath))

    if update_nav:
        update_mkdocs_file(create_nav_menu_yaml(nav_items))
    if created:
        LOGGER.info(f"Created {created} new reference files")
    if _missing_type_warnings:
        LOGGER.warning(f"{len(_missing_type_warnings)} functions/methods have parameters missing type annotations:")
        for warning in _missing_type_warnings:
            LOGGER.warning(f"  - {warning}")
        raise ValueError(
            f"{len(_missing_type_warnings)} parameters missing types in both signature and docstring. "
            f"Add type annotations to the function signature or (type) in the docstring Args section."
        )
    return nav_items
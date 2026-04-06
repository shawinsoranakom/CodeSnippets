def iter_all_lang_paths(lang_path_root: Path) -> Iterable[Path]:
    """
    Iterate on the markdown files to translate in order of priority.
    """

    first_dirs = [
        lang_path_root / "learn",
        lang_path_root / "tutorial",
        lang_path_root / "advanced",
        lang_path_root / "about",
        lang_path_root / "how-to",
    ]
    first_parent = lang_path_root
    yield from first_parent.glob("*.md")
    for dir_path in first_dirs:
        yield from dir_path.rglob("*.md")
    first_dirs_str = tuple(str(d) for d in first_dirs)
    for path in lang_path_root.rglob("*.md"):
        if str(path).startswith(first_dirs_str):
            continue
        if path.parent == first_parent:
            continue
        yield path
def iter_all_en_paths() -> Iterable[Path]:
    """
    Iterate on the markdown files to translate in order of priority.
    """
    first_dirs = [
        Path("docs/en/docs/learn"),
        Path("docs/en/docs/tutorial"),
        Path("docs/en/docs/advanced"),
        Path("docs/en/docs/about"),
        Path("docs/en/docs/how-to"),
    ]
    first_parent = Path("docs/en/docs")
    yield from first_parent.glob("*.md")
    for dir_path in first_dirs:
        yield from dir_path.rglob("*.md")
    first_dirs_str = tuple(str(d) for d in first_dirs)
    for path in Path("docs/en/docs").rglob("*.md"):
        if str(path).startswith(first_dirs_str):
            continue
        if path.parent == first_parent:
            continue
        yield path
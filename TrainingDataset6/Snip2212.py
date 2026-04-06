def _get_all_environments():
    root = Path('~/.virtualenvs').expanduser()
    if not root.is_dir():
        return

    for child in root.iterdir():
        if child.is_dir():
            yield child.name
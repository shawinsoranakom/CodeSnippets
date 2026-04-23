def resolve_destination_from_tags(tags: list[str]) -> tuple[str, list[str]]:
    """Validates and maps tags -> (base_dir, subdirs_for_fs)"""
    if not tags:
        raise ValueError("tags must not be empty")
    root = tags[0].lower()
    if root == "models":
        if len(tags) < 2:
            raise ValueError("at least two tags required for model asset")
        try:
            bases = folder_paths.folder_names_and_paths[tags[1]][0]
        except KeyError:
            raise ValueError(f"unknown model category '{tags[1]}'")
        if not bases:
            raise ValueError(f"no base path configured for category '{tags[1]}'")
        base_dir = os.path.abspath(bases[0])
        raw_subdirs = tags[2:]
    elif root == "input":
        base_dir = os.path.abspath(folder_paths.get_input_directory())
        raw_subdirs = tags[1:]
    elif root == "output":
        base_dir = os.path.abspath(folder_paths.get_output_directory())
        raw_subdirs = tags[1:]
    else:
        raise ValueError(f"unknown root tag '{tags[0]}'; expected 'models', 'input', or 'output'")
    _sep_chars = frozenset(("/", "\\", os.sep))
    for i in raw_subdirs:
        if i in (".", "..") or _sep_chars & set(i):
            raise ValueError("invalid path component in tags")

    return base_dir, raw_subdirs if raw_subdirs else []
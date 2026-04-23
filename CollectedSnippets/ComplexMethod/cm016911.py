def list_files_recursively(base_dir: str) -> list[str]:
    """Recursively list all files in a directory, following symlinks."""
    out: list[str] = []
    base_abs = os.path.abspath(base_dir)
    if not os.path.isdir(base_abs):
        return out
    # Track seen real directory identities to prevent circular symlink loops
    seen_dirs: set[tuple[int, int]] = set()
    for dirpath, subdirs, filenames in os.walk(
        base_abs, topdown=True, followlinks=True
    ):
        try:
            st = os.stat(dirpath)
            dir_id = (st.st_dev, st.st_ino)
        except OSError:
            subdirs.clear()
            continue
        if dir_id in seen_dirs:
            subdirs.clear()
            continue
        seen_dirs.add(dir_id)
        subdirs[:] = [d for d in subdirs if is_visible(d)]
        for name in filenames:
            if not is_visible(name):
                continue
            out.append(os.path.abspath(os.path.join(dirpath, name)))
    return out
def _dirfiles(dir_path: str, glob_pattern: str) -> str:
    p = Path(dir_path)
    filenames = sorted(
        [f.name for f in p.glob(glob_pattern) if not f.name.startswith(".")]
    )
    return "+".join(filenames)
def _is_valid_path(path: Optional[str]) -> bool:
    return isinstance(path, str) and (os.path.isfile(path) or os.path.isdir(path))
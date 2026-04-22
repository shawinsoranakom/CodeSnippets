def watch_file(
    path: str,
    on_file_changed: Callable[[str], None],
    watcher_type: Optional[str] = None,
) -> bool:
    return _watch_path(path, on_file_changed, watcher_type)
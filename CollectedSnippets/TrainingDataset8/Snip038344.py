def watch_dir(
    path: str,
    on_dir_changed: Callable[[str], None],
    watcher_type: Optional[str] = None,
    *,  # keyword-only arguments:
    glob_pattern: Optional[str] = None,
    allow_nonexistent: bool = False,
) -> bool:
    return _watch_path(
        path,
        on_dir_changed,
        watcher_type,
        glob_pattern=glob_pattern,
        allow_nonexistent=allow_nonexistent,
    )
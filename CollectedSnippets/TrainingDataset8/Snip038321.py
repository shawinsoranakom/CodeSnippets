def add_path_change_listener(
        self,
        path: str,
        callback: Callable[[str], None],
        *,  # keyword-only arguments:
        glob_pattern: Optional[str] = None,
        allow_nonexistent: bool = False,
    ) -> None:
        """Add a path to this object's event filter."""
        with self._lock:
            watched_path = self._watched_paths.get(path, None)
            if watched_path is None:
                md5 = util.calc_md5_with_blocking_retries(
                    path,
                    glob_pattern=glob_pattern,
                    allow_nonexistent=allow_nonexistent,
                )
                modification_time = util.path_modification_time(path, allow_nonexistent)
                watched_path = WatchedPath(
                    md5=md5,
                    modification_time=modification_time,
                    glob_pattern=glob_pattern,
                    allow_nonexistent=allow_nonexistent,
                )
                self._watched_paths[path] = watched_path

            watched_path.on_changed.connect(callback, weak=False)
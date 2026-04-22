def __init__(
        self,
        path: str,
        on_changed: Callable[[str], None],
        *,  # keyword-only arguments:
        glob_pattern: Optional[str] = None,
        allow_nonexistent: bool = False,
    ) -> None:
        """Constructor for EventBasedPathWatchers.

        Parameters
        ----------
        path : str
            The path to watch.
        on_changed : Callable[[str], None]
            Callback to call when the path changes.
        glob_pattern : Optional[str]
            A glob pattern to filter the files in a directory that should be
            watched. Only relevant when creating an EventBasedPathWatcher on a
            directory.
        allow_nonexistent : bool
            If True, the watcher will not raise an exception if the path does
            not exist. This can be used to watch for the creation of a file or
            directory at a given path.
        """
        self._path = os.path.abspath(path)
        self._on_changed = on_changed

        path_watcher = _MultiPathWatcher.get_singleton()
        path_watcher.watch_path(
            self._path,
            on_changed,
            glob_pattern=glob_pattern,
            allow_nonexistent=allow_nonexistent,
        )
        LOGGER.debug("Watcher created for %s", self._path)
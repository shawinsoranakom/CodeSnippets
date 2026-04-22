def __init__(
        self,
        path: str,
        on_changed: Callable[[str], None],
        *,  # keyword-only arguments:
        glob_pattern: Optional[str] = None,
        allow_nonexistent: bool = False,
    ) -> None:
        """Constructor.

        You do not need to retain a reference to a PollingPathWatcher to
        prevent it from being garbage collected. (The global _executor object
        retains references to all active instances.)
        """
        # TODO(vdonato): Modernize this by switching to pathlib.
        self._path = path
        self._on_changed = on_changed

        self._glob_pattern = glob_pattern
        self._allow_nonexistent = allow_nonexistent

        self._active = True

        self._modification_time = util.path_modification_time(
            self._path, self._allow_nonexistent
        )
        self._md5 = util.calc_md5_with_blocking_retries(
            self._path,
            glob_pattern=self._glob_pattern,
            allow_nonexistent=self._allow_nonexistent,
        )
        self._schedule()
def _check_if_path_changed(self) -> None:
        if not self._active:
            # Don't call self._schedule()
            return

        modification_time = util.path_modification_time(
            self._path, self._allow_nonexistent
        )
        if modification_time <= self._modification_time:
            self._schedule()
            return

        self._modification_time = modification_time

        md5 = util.calc_md5_with_blocking_retries(
            self._path,
            glob_pattern=self._glob_pattern,
            allow_nonexistent=self._allow_nonexistent,
        )
        if md5 == self._md5:
            self._schedule()
            return

        self._md5 = md5

        LOGGER.debug("Change detected: %s", self._path)
        self._on_changed(self._path)

        self._schedule()
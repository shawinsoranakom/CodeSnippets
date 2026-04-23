def _on_secrets_file_changed(self, _) -> None:
        with self._lock:
            _LOGGER.debug("Secrets file %s changed, reloading", self._file_path)
            self._reset()
            self._parse(print_exceptions=True)

        # Emit a signal to notify receivers that the `secrets.toml` file
        # has been changed.
        self._file_change_listener.send()
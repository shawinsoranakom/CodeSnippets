def _maybe_install_file_watcher(self) -> None:
        with self._lock:
            if self._file_watcher_installed:
                return

            # We force our watcher_type to 'poll' because Streamlit Cloud
            # stores `secrets.toml` in a virtual filesystem that is
            # incompatible with watchdog.
            streamlit.watcher.path_watcher.watch_file(
                self._file_path,
                self._on_secrets_file_changed,
                watcher_type="poll",
            )

            # We set file_watcher_installed to True even if watch_file
            # returns False to avoid repeatedly trying to install it.
            self._file_watcher_installed = True
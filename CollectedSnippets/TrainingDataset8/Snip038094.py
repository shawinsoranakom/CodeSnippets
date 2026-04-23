def _reset(self) -> None:
        """Clear the secrets dictionary and remove any secrets that were
        added to os.environ.

        Thread-safe.
        """
        with self._lock:
            if self._secrets is None:
                return

            for k, v in self._secrets.items():
                self._maybe_delete_environment_variable(k, v)
            self._secrets = None
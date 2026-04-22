def _parse(self, print_exceptions: bool) -> Mapping[str, Any]:
        """Parse our secrets.toml file if it's not already parsed.
        This function is safe to call from multiple threads.

        Parameters
        ----------
        print_exceptions : bool
            If True, then exceptions will be printed with `st.error` before
            being re-raised.

        Raises
        ------
        FileNotFoundError
            Raised if secrets.toml doesn't exist.

        """
        # Avoid taking a lock for the common case where secrets are already
        # loaded.
        secrets = self._secrets
        if secrets is not None:
            return secrets

        with self._lock:
            if self._secrets is not None:
                return self._secrets

            try:
                with open(self._file_path, encoding="utf-8") as f:
                    secrets_file_str = f.read()
            except FileNotFoundError:
                if print_exceptions:
                    st.error(f"Secrets file not found. Expected at: {self._file_path}")
                raise

            try:
                secrets = toml.loads(secrets_file_str)
            except:
                if print_exceptions:
                    st.error("Error parsing Secrets file.")
                raise

            for k, v in secrets.items():
                self._maybe_set_environment_variable(k, v)

            self._secrets = secrets
            self._maybe_install_file_watcher()

            return self._secrets
def load_if_toml_exists(self) -> None:
        """Load secrets.toml from disk if it exists. If it doesn't exist,
        no exception will be raised. (If the file exists but is malformed,
        an exception *will* be raised.)

        Thread-safe.
        """
        try:
            self._parse(print_exceptions=False)
        except FileNotFoundError:
            # No secrets.toml file exists. That's fine.
            pass
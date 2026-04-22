def close(self) -> None:
        """Stop watching the file system."""
        self._active = False
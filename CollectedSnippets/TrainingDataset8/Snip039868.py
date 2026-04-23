def join(self) -> None:
        """Join the script_thread if it's running."""
        if self._script_thread is not None:
            self._script_thread.join()
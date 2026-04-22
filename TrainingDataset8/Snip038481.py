def assert_no_unhandled_exception(self) -> None:
        """If the thread target raised an unhandled exception, re-raise it.
        Otherwise no-op.
        """
        if self._unhandled_exception is not None:
            raise RuntimeError(
                f"Unhandled exception in thread '{self.name}'"
            ) from self._unhandled_exception
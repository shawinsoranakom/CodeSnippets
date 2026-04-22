def clear_all(self) -> None:
        """Clear all singleton caches."""
        with self._caches_lock:
            self._function_caches = {}
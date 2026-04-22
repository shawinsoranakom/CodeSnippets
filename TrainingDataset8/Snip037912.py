def clear(self) -> None:
        """Clear all caches"""
        with self._lock:
            self._function_caches = {}
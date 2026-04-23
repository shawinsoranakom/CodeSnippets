def __contains__(self, key: str) -> bool:
        with self._lock:
            if self._disconnected:
                return False

            return key in self._state
def __delitem__(self, key: str) -> None:
        with self._lock:
            if self._disconnected:
                raise KeyError(key)

            del self._state[key]
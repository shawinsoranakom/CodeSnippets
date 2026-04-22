def __getitem__(self, key: str) -> Any:
        with self._lock:
            if self._disconnected:
                raise KeyError(key)

            return self._state[key]
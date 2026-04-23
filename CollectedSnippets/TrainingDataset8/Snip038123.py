def __setitem__(self, key: str, value: Any) -> None:
        with self._lock:
            if self._disconnected:
                return

            self._state[key] = value
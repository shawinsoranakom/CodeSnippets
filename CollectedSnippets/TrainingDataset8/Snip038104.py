def has_key(self, k: str) -> bool:
        """True if the given key is in the dict. Thread-safe."""
        return k in self._parse(True)
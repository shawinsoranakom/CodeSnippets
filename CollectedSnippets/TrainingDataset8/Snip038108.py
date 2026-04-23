def __contains__(self, key: Any) -> bool:
        """True if the given key is in the dict. Thread-safe."""
        return key in self._parse(True)
def keys(self) -> KeysView[str]:
        """A view of the keys in the dict. Thread-safe."""
        return self._parse(True).keys()
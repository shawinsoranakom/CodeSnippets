def __len__(self) -> int:
        """The number of entries in the dict. Thread-safe."""
        return len(self._parse(True))
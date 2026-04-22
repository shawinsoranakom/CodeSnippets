def __iter__(self) -> Iterator[str]:
        """An iterator over the keys in the dict. Thread-safe."""
        return iter(self._parse(True))
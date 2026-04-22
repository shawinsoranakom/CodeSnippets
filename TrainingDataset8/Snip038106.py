def values(self) -> ValuesView[Any]:
        """A view of the values in the dict. Thread-safe."""
        return self._parse(True).values()
def items(self) -> ItemsView[str, Any]:
        """A view of the key-value items in the dict. Thread-safe."""
        return self._parse(True).items()
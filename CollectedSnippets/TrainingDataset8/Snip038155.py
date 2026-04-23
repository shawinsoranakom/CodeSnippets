def __len__(self) -> int:
        """Return the number of items in SessionState."""
        return len(self._keys())
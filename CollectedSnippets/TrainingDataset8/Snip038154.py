def __iter__(self) -> Iterator[Any]:
        """Return an iterator over the keys of the SessionState.
        This is a shortcut for `iter(self.keys())`
        """
        return iter(self._keys())
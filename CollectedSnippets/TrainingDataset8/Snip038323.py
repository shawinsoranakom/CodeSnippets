def is_watching_paths(self) -> bool:
        """Return true if this object has 1+ paths in its event filter."""
        return len(self._watched_paths) > 0
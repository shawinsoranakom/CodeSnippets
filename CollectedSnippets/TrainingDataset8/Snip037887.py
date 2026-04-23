def clear(self) -> None:
        """Clear the queue."""
        self._queue = []
        self._delta_index_map = dict()
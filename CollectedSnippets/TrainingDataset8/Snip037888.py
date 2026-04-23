def flush(self) -> List[ForwardMsg]:
        """Clear the queue and return a list of the messages it contained
        before being cleared."""
        queue = self._queue
        self.clear()
        return queue
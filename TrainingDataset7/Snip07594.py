def __contains__(self, item):
        return item in self._loaded_messages or item in self._queued_messages
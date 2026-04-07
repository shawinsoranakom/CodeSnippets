def __len__(self):
        return len(self._loaded_messages) + len(self._queued_messages)
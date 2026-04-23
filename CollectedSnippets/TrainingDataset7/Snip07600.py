def update(self, response):
        """
        Store all unread messages.

        If the backend has yet to be iterated, store previously stored messages
        again. Otherwise, only store messages added after the last iteration.
        """
        self._prepare_messages(self._queued_messages)
        if self.used:
            return self._store(self._queued_messages, response)
        elif self.added_new:
            messages = self._loaded_messages + self._queued_messages
            return self._store(messages, response)
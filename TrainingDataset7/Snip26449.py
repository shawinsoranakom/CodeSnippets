def stored_messages_count(self, storage, response):
        """
        Return the number of messages being stored after a
        ``storage.update()`` call.
        """
        raise NotImplementedError("This method must be set by a subclass.")
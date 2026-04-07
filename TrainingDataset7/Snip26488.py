def stored_messages_count(self, storage, response):
        """
        Return the storage totals from both cookie and session backends.
        """
        return self.stored_cookie_messages_count(
            storage, response
        ) + self.stored_session_messages_count(storage, response)
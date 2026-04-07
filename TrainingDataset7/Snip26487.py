def stored_session_messages_count(self, storage, response):
        return stored_session_messages_count(self.get_session_storage(storage))
def stored_cookie_messages_count(self, storage, response):
        return stored_cookie_messages_count(self.get_cookie_storage(storage), response)
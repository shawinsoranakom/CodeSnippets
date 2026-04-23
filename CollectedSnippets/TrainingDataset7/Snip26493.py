def test_flush_used_backends(self):
        request = self.get_request()
        storage = self.storage_class(request)
        cookie_storage = self.get_cookie_storage(storage)
        session_storage = self.get_session_storage(storage)
        # Set initial cookie and session data.
        set_cookie_data(cookie_storage, ["cookie", CookieStorage.not_finished])
        set_session_data(session_storage, ["session"])
        # When updating, previously used but no longer needed backends are
        # flushed.
        response = self.get_response()
        list(storage)
        storage.update(response)
        session_storing = self.stored_session_messages_count(storage, response)
        self.assertEqual(session_storing, 0)
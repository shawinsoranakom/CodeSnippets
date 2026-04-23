def test_no_fallback(self):
        """
        (1) A short number of messages whose data size doesn't exceed what is
        allowed in a cookie will all be stored in the CookieBackend.

        (2) If the CookieBackend can store all messages, the SessionBackend
        won't be written to at all.
        """
        storage = self.get_storage()
        response = self.get_response()
        # Overwrite the _store method of the fallback storage to prove it isn't
        # used (it would cause a TypeError: 'NoneType' object is not callable).
        self.get_session_storage(storage)._store = None
        for i in range(5):
            storage.add(constants.INFO, str(i) * 100)
        storage.update(response)
        cookie_storing = self.stored_cookie_messages_count(storage, response)
        self.assertEqual(cookie_storing, 5)
        session_storing = self.stored_session_messages_count(storage, response)
        self.assertEqual(session_storing, 0)
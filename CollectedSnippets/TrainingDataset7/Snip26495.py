def test_session_fallback(self):
        """
        If the data exceeds what is allowed in a cookie, messages which did
        not fit are stored in the SessionBackend.
        """
        storage = self.get_storage()
        response = self.get_response()
        # see comment in CookieTests.test_cookie_max_length()
        msg_size = int((CookieStorage.max_cookie_size - 54) / 4.5 - 37)
        # Generate the same (tested) content every time that does not get run
        # through zlib compression.
        random.seed(42)
        for i in range(5):
            storage.add(constants.INFO, get_random_string(msg_size))
        storage.update(response)
        cookie_storing = self.stored_cookie_messages_count(storage, response)
        self.assertEqual(cookie_storing, 4)
        session_storing = self.stored_session_messages_count(storage, response)
        self.assertEqual(session_storing, 1)
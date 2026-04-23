def test_session_fallback_only(self):
        """
        Large messages, none of which fit in a cookie, are stored in the
        SessionBackend (and nothing is stored in the CookieBackend).
        """
        storage = self.get_storage()
        response = self.get_response()
        # Generate the same (tested) content every time that does not get run
        # through zlib compression.
        random.seed(42)
        storage.add(constants.INFO, get_random_string(5000))
        storage.update(response)
        cookie_storing = self.stored_cookie_messages_count(storage, response)
        self.assertEqual(cookie_storing, 0)
        session_storing = self.stored_session_messages_count(storage, response)
        self.assertEqual(session_storing, 1)
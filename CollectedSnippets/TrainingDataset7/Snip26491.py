def test_get_fallback(self):
        request = self.get_request()
        storage = self.storage_class(request)
        cookie_storage = self.get_cookie_storage(storage)
        session_storage = self.get_session_storage(storage)

        # Set initial cookie and session data.
        example_messages = [str(i) for i in range(5)]
        set_cookie_data(
            cookie_storage, example_messages[:4] + [CookieStorage.not_finished]
        )
        set_session_data(session_storage, example_messages[4:])
        self.assertEqual(list(storage), example_messages)
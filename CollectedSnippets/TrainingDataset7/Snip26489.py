def test_get(self):
        request = self.get_request()
        storage = self.storage_class(request)
        cookie_storage = self.get_cookie_storage(storage)
        # Set initial cookie data.
        example_messages = [str(i) for i in range(5)]
        set_cookie_data(cookie_storage, example_messages)
        # Overwrite the _get method of the fallback storage to prove it is not
        # used (it would cause a TypeError: 'NoneType' object is not callable).
        self.get_session_storage(storage)._get = None
        self.assertEqual(list(storage), example_messages)
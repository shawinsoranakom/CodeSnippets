def test_get_bad_cookie(self):
        request = self.get_request()
        storage = self.storage_class(request)
        # Set initial (invalid) data.
        example_messages = ["test", "me"]
        set_cookie_data(storage, example_messages, invalid=True)
        # The message actually contains what we expect.
        self.assertEqual(list(storage), [])
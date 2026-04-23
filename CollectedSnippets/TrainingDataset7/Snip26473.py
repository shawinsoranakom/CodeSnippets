def test_get(self):
        storage = self.storage_class(self.get_request())
        # Set initial data.
        example_messages = ["test", "me"]
        set_cookie_data(storage, example_messages)
        # The message contains what's expected.
        self.assertEqual(list(storage), example_messages)
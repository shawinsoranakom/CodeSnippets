def test_get(self):
        storage = self.storage_class(self.get_request())
        example_messages = ["test", "me"]
        set_session_data(storage, example_messages)
        self.assertEqual(list(storage), example_messages)
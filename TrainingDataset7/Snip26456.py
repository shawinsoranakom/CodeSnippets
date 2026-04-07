def test_high_level(self):
        request = self.get_request()
        storage = self.storage_class(request)
        request._messages = storage

        self.assertTrue(set_level(request, 30))
        self.assertEqual(get_level(request), 30)

        add_level_messages(storage)
        self.assertEqual(len(storage), 2)
def test_add(self):
        storage = self.get_storage()
        self.assertFalse(storage.added_new)
        storage.add(constants.INFO, "Test message 1")
        self.assertTrue(storage.added_new)
        storage.add(constants.INFO, "Test message 2", extra_tags="tag")
        self.assertEqual(len(storage), 2)
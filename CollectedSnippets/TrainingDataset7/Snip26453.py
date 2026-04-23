def test_existing_add(self):
        storage = self.get_existing_storage()
        self.assertFalse(storage.added_new)
        storage.add(constants.INFO, "Test message 3")
        self.assertTrue(storage.added_new)
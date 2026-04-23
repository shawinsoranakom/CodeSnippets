def test_add_update(self):
        storage = self.get_storage()
        response = self.get_response()

        storage.add(constants.INFO, "Test message 1")
        storage.add(constants.INFO, "Test message 1", extra_tags="tag")
        storage.update(response)

        storing = self.stored_messages_count(storage, response)
        self.assertEqual(storing, 2)
def test_existing_read_add_update(self):
        storage = self.get_existing_storage()
        response = self.get_response()

        list(storage)  # Simulates a read
        storage.add(constants.INFO, "Test message 3")
        storage.update(response)

        storing = self.stored_messages_count(storage, response)
        self.assertEqual(storing, 1)
def test_existing_add_read_update(self):
        storage = self.get_existing_storage()
        response = self.get_response()

        storage.add(constants.INFO, "Test message 3")
        list(storage)  # Simulates a read
        storage.update(response)

        storing = self.stored_messages_count(storage, response)
        self.assertEqual(storing, 0)
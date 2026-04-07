def test_add_lazy_translation(self):
        storage = self.get_storage()
        response = self.get_response()

        storage.add(constants.INFO, gettext_lazy("lazy message"))
        storage.update(response)

        storing = self.stored_messages_count(storage, response)
        self.assertEqual(storing, 1)
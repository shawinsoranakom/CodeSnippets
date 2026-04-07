def test_tags(self):
        storage = self.get_storage()
        storage.level = 0
        add_level_messages(storage)
        storage.add(constants.INFO, "A generic info message", extra_tags=None)
        tags = [msg.tags for msg in storage]
        self.assertEqual(
            tags, ["info", "", "extra-tag debug", "warning", "error", "success", "info"]
        )
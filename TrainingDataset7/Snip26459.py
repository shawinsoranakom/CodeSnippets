def test_level_tag(self):
        storage = self.get_storage()
        storage.level = 0
        add_level_messages(storage)
        tags = [msg.level_tag for msg in storage]
        self.assertEqual(tags, ["info", "", "debug", "warning", "error", "success"])
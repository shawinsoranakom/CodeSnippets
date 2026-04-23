def test_custom_tags(self):
        storage = self.get_storage()
        storage.level = 0
        add_level_messages(storage)
        tags = [msg.tags for msg in storage]
        self.assertEqual(tags, ["info", "custom", "extra-tag", "", "bad", "success"])
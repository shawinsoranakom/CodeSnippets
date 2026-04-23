def test_empty_string(self):
        self.assertEqual(default_if_none("", "default"), "")
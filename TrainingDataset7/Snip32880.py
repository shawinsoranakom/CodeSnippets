def test_empty_string(self):
        self.assertEqual(default("", "default"), "default")
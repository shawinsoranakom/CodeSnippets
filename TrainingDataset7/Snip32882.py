def test_none(self):
        self.assertEqual(default_if_none(None, "default"), "default")
def test_none(self):
        self.assertEqual(default(None, "default"), "default")
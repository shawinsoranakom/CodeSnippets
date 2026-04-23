def test_value(self):
        self.assertEqual(default_if_none("val", "default"), "val")
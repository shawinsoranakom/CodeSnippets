def test_value(self):
        self.assertEqual(default("val", "default"), "val")
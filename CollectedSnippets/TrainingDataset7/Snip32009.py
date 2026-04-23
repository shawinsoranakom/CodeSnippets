def test_override(self):
        self.assertEqual(settings.ITEMS, ["b", "c", "d"])
        self.assertEqual(settings.TEST, "override")
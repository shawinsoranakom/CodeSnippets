def test_override(self):
        self.assertEqual(settings.ITEMS, ["b", "c", "d"])
        self.assertEqual(settings.ITEMS_OUTER, [1, 2, 3])
        self.assertEqual(settings.TEST, "override")
        self.assertEqual(settings.TEST_OUTER, "outer")
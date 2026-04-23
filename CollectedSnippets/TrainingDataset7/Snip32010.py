def test_method_override(self):
        self.assertEqual(settings.ITEMS, ["a", "b", "d", "e"])
        self.assertEqual(settings.TEST, "override2")
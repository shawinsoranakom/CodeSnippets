def test_method_list_override(self):
        self.assertEqual(settings.ITEMS, ["a", "b", "e", "f"])
        self.assertEqual(settings.ITEMS_OUTER, [1, 2, 3])
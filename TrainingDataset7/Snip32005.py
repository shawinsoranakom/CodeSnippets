def test_method_list_override_nested_order(self):
        self.assertEqual(settings.ITEMS, ["d", "c", "b"])
def test_empty_group_by_cols(self):
        window = Window(expression=Sum("pk"))
        self.assertEqual(window.get_group_by_cols(), [])
        self.assertFalse(window.contains_aggregate)
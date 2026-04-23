def test_list_display_for_value_empty(self):
        for value in EMPTY_VALUES:
            with self.subTest(empty_value=value):
                display_value = display_for_value(value, self.empty_value)
                self.assertEqual(display_value, self.empty_value)
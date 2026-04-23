def test_list_display_for_value(self):
        display_value = display_for_value([1, 2, 3], self.empty_value)
        self.assertEqual(display_value, "1, 2, 3")

        display_value = display_for_value(
            [1, 2, "buckle", "my", "shoe"], self.empty_value
        )
        self.assertEqual(display_value, "1, 2, buckle, my, shoe")
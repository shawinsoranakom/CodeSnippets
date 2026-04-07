def test_list_display_for_value_consecutive_whitespace(self):
        cases = [
            ("   ", "-empty-"),
            ("        cheeze", "cheeze"),
            ("pizza       ", "pizza"),
            ("       chicken        ", "chicken"),
            (mark_safe("  <em>soy chicken</em>  "), "  <em>soy chicken</em>  "),
        ]
        for value, expect_display_value in cases:
            with self.subTest(value=value):
                display_value = display_for_value(value, self.empty_value)
                self.assertEqual(display_value, expect_display_value)
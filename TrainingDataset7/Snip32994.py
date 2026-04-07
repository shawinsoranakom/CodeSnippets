def test_non_string_input(self):
        self.assertEqual(linebreaks_filter(123), "<p>123</p>")
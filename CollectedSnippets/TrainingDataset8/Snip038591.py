def test_maybe_convert_to_number(self):
        self.assertEqual(1234, config._maybe_convert_to_number("1234"))
        self.assertEqual(1234.5678, config._maybe_convert_to_number("1234.5678"))
        self.assertEqual("1234.5678ex", config._maybe_convert_to_number("1234.5678ex"))
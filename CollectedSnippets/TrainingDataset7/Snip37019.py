def test_get_formats(self):
        formats = get_formats()
        # Test 3 possible types in get_formats: integer, string, and list.
        self.assertEqual(formats["FIRST_DAY_OF_WEEK"], 1)
        self.assertEqual(formats["DECIMAL_SEPARATOR"], ",")
        self.assertEqual(
            formats["TIME_INPUT_FORMATS"], ["%H:%M:%S", "%H:%M:%S.%f", "%H:%M"]
        )
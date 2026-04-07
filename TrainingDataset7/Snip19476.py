def test_get_warning_for_invalid_pattern_tuple(self):
        warning = get_warning_for_invalid_pattern((r"^$", lambda x: x))[0]
        self.assertEqual(warning.hint, "Try using path() instead of a tuple.")
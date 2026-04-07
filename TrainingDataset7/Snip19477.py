def test_get_warning_for_invalid_pattern_other(self):
        warning = get_warning_for_invalid_pattern(object())[0]
        self.assertIsNone(warning.hint)
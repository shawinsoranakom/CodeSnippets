def test_get_warning_for_invalid_pattern_string(self):
        warning = get_warning_for_invalid_pattern("")[0]
        self.assertEqual(
            warning.hint,
            "Try removing the string ''. The list of urlpatterns should "
            "not have a prefix string as the first element.",
        )
def test_regex_equality_blank(self):
        self.assertEqual(
            RegexValidator(),
            RegexValidator(),
        )
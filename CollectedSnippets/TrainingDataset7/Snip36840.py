def test_regex_equality_nocache(self):
        pattern = r"^(?:[a-z0-9.-]*)://"
        left = RegexValidator(pattern)
        re.purge()
        right = RegexValidator(pattern)

        self.assertEqual(
            left,
            right,
        )
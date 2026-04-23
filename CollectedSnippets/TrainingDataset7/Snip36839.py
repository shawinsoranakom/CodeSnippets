def test_regex_equality(self):
        self.assertEqual(
            RegexValidator(r"^(?:[a-z0-9.-]*)://"),
            RegexValidator(r"^(?:[a-z0-9.-]*)://"),
        )
        self.assertNotEqual(
            RegexValidator(r"^(?:[a-z0-9.-]*)://"),
            RegexValidator(r"^(?:[0-9.-]*)://"),
        )
        self.assertEqual(
            RegexValidator(r"^(?:[a-z0-9.-]*)://", "oh noes", "invalid"),
            RegexValidator(r"^(?:[a-z0-9.-]*)://", "oh noes", "invalid"),
        )
        self.assertNotEqual(
            RegexValidator(r"^(?:[a-z0-9.-]*)://", "oh", "invalid"),
            RegexValidator(r"^(?:[a-z0-9.-]*)://", "oh noes", "invalid"),
        )
        self.assertNotEqual(
            RegexValidator(r"^(?:[a-z0-9.-]*)://", "oh noes", "invalid"),
            RegexValidator(r"^(?:[a-z0-9.-]*)://"),
        )

        self.assertNotEqual(
            RegexValidator("", flags=re.IGNORECASE),
            RegexValidator(""),
        )

        self.assertNotEqual(
            RegexValidator(""),
            RegexValidator("", inverse_match=True),
        )
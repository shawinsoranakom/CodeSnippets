def test_regex_validator_flags(self):
        msg = "If the flags are set, regex must be a regular expression string."
        with self.assertRaisesMessage(TypeError, msg):
            RegexValidator(re.compile("a"), flags=re.IGNORECASE)
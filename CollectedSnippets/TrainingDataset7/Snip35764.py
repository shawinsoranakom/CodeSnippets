def test_access_locale_regex_descriptor(self):
        self.assertIsInstance(RegexPattern.regex, LocaleRegexDescriptor)
def test_regex_compile_error(self):
        """Regex errors are re-raised as ImproperlyConfigured."""
        provider = RegexPattern("*")
        msg = '"*" is not a valid regular expression: nothing to repeat'
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            provider.regex
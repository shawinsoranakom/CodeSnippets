def test_domain_name_with_whitespaces(self):
        # Regression for #17320
        # Domain names are not allowed contain whitespace characters
        site = Site(name="test name", domain="test test")
        with self.assertRaises(ValidationError):
            site.full_clean()
        site.domain = "test\ttest"
        with self.assertRaises(ValidationError):
            site.full_clean()
        site.domain = "test\ntest"
        with self.assertRaises(ValidationError):
            site.full_clean()
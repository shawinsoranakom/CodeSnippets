def test_unified(self):
        """--output=unified emits settings diff in unified mode."""
        self.write_settings("settings_to_diff.py", sdict={"FOO": '"bar"'})
        args = ["diffsettings", "--settings=settings_to_diff", "--output=unified"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertOutput(out, "+ FOO = 'bar'")
        self.assertOutput(out, "- SECRET_KEY = ''")
        self.assertOutput(out, "+ SECRET_KEY = 'django_tests_secret_key'")
        self.assertNotInOutput(out, "  APPEND_SLASH = True")
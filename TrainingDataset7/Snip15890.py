def test_basic(self):
        """Runs without error and emits settings diff."""
        self.write_settings("settings_to_diff.py", sdict={"FOO": '"bar"'})
        args = ["diffsettings", "--settings=settings_to_diff"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertOutput(out, "FOO = 'bar'  ###")
        # Attributes from django.conf.Settings don't appear.
        self.assertNotInOutput(out, "is_overridden = ")
def test_all(self):
        """The all option also shows settings with the default value."""
        self.write_settings("settings_to_diff.py", sdict={"STATIC_URL": "None"})
        args = ["diffsettings", "--settings=settings_to_diff", "--all"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertOutput(out, "### STATIC_URL = None")
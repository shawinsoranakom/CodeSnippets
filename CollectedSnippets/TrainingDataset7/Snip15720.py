def test_builtin_with_bad_environment(self):
        """
        no settings: manage.py builtin commands fail if settings file (from
        environment) doesn't exist.
        """
        args = ["check", "admin_scripts"]
        out, err = self.run_manage(args, "bad_settings")
        self.assertNoOutput(out)
        self.assertOutput(err, "No module named '?bad_settings'?", regex=True)
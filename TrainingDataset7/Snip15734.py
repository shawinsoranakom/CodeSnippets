def test_builtin_with_bad_settings(self):
        """
        fulldefault: manage.py builtin commands succeed if settings file (from
        argument) doesn't exist.
        """
        args = ["check", "--settings=bad_settings", "admin_scripts"]
        out, err = self.run_manage(args)
        self.assertNoOutput(out)
        self.assertOutput(err, "No module named '?bad_settings'?", regex=True)
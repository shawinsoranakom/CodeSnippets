def test_builtin_with_settings(self):
        """
        minimal: manage.py builtin commands fail if settings are provided as
        argument
        """
        args = ["check", "--settings=test_project.settings", "admin_scripts"]
        out, err = self.run_manage(args)
        self.assertNoOutput(out)
        self.assertOutput(err, "No installed app with label 'admin_scripts'.")
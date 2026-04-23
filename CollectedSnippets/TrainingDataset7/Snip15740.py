def test_builtin_command(self):
        """
        minimal: manage.py builtin commands fail with an error when no settings
        provided.
        """
        args = ["check", "admin_scripts"]
        out, err = self.run_manage(args)
        self.assertNoOutput(out)
        self.assertOutput(err, "No installed app with label 'admin_scripts'.")
def test_builtin_with_environment(self):
        """
        minimal: django-admin builtin commands fail if settings are provided in
        the environment.
        """
        args = ["check", "admin_scripts"]
        out, err = self.run_django_admin(args, "test_project.settings")
        self.assertNoOutput(out)
        self.assertOutput(err, "No installed app with label 'admin_scripts'.")
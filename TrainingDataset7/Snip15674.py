def test_builtin_with_environment(self):
        """
        fulldefault: django-admin builtin commands succeed if the environment
        contains settings.
        """
        args = ["check", "admin_scripts"]
        out, err = self.run_django_admin(args, "test_project.settings")
        self.assertNoOutput(err)
        self.assertOutput(out, SYSTEM_CHECK_MSG)
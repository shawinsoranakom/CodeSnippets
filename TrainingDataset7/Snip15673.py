def test_builtin_with_settings(self):
        """
        fulldefault: django-admin builtin commands succeed if a settings file
        is provided.
        """
        args = ["check", "--settings=test_project.settings", "admin_scripts"]
        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        self.assertOutput(out, SYSTEM_CHECK_MSG)
def test_builtin_command(self):
        """
        default: django-admin builtin commands fail with an error when no
        settings provided.
        """
        args = ["check", "admin_scripts"]
        out, err = self.run_django_admin(args)
        self.assertNoOutput(out)
        self.assertOutput(err, "settings are not configured")
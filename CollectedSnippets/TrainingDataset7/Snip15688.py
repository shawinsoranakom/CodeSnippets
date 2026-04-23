def test_custom_command_with_environment(self):
        """
        minimal: django-admin can't execute user commands, even if settings are
        provided in environment.
        """
        args = ["noargs_command"]
        out, err = self.run_django_admin(args, "test_project.settings")
        self.assertNoOutput(out)
        self.assertOutput(err, "Unknown command: 'noargs_command'")
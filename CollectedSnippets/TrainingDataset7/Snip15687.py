def test_custom_command_with_settings(self):
        """
        minimal: django-admin can't execute user commands, even if settings are
        provided as argument.
        """
        args = ["noargs_command", "--settings=test_project.settings"]
        out, err = self.run_django_admin(args)
        self.assertNoOutput(out)
        self.assertOutput(err, "Unknown command: 'noargs_command'")
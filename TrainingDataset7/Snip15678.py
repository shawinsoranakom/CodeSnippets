def test_custom_command_with_settings(self):
        """
        fulldefault: django-admin can execute user commands if settings are
        provided as argument.
        """
        args = ["noargs_command", "--settings=test_project.settings"]
        out, err = self.run_django_admin(args)
        self.assertNoOutput(err)
        self.assertOutput(out, "EXECUTE: noargs_command")
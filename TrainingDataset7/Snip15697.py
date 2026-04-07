def test_custom_command_with_environment(self):
        """
        alternate: django-admin can execute user commands if settings are
        provided in environment.
        """
        args = ["noargs_command"]
        out, err = self.run_django_admin(args, "test_project.alternate_settings")
        self.assertNoOutput(err)
        self.assertOutput(out, "EXECUTE: noargs_command")
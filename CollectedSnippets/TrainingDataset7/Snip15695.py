def test_custom_command(self):
        """
        alternate: django-admin can't execute user commands unless settings
        are provided.
        """
        args = ["noargs_command"]
        out, err = self.run_django_admin(args)
        self.assertNoOutput(out)
        self.assertOutput(err, "No Django settings specified")
        self.assertOutput(err, "Unknown command: 'noargs_command'")
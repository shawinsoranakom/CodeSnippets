def test_custom_command_with_environment(self):
        """
        minimal: manage.py can't execute user commands, even if settings are
        provided in environment.
        """
        args = ["noargs_command"]
        out, err = self.run_manage(args, "test_project.settings")
        self.assertNoOutput(out)
        self.assertOutput(err, "Unknown command: 'noargs_command'")
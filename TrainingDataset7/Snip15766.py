def test_custom_command_with_environment(self):
        """
        multiple: manage.py can execute user commands if settings are provided
        in environment.
        """
        args = ["noargs_command"]
        out, err = self.run_manage(args, "alternate_settings")
        self.assertNoOutput(err)
        self.assertOutput(out, "EXECUTE: noargs_command")
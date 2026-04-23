def test_custom_command_with_settings(self):
        """
        multiple: manage.py can execute user commands if settings are provided
        as argument.
        """
        args = ["noargs_command", "--settings=alternate_settings"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertOutput(out, "EXECUTE: noargs_command")
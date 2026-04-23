def test_custom_command_with_settings(self):
        """
        alternate: manage.py can execute user commands if settings are provided
        as argument
        """
        args = ["noargs_command", "--settings=alternate_settings"]
        out, err = self.run_manage(args)
        self.assertOutput(
            out,
            "EXECUTE: noargs_command options=[('force_color', False), "
            "('no_color', False), ('pythonpath', None), ('settings', "
            "'alternate_settings'), ('traceback', False), ('verbosity', 1)]",
        )
        self.assertNoOutput(err)
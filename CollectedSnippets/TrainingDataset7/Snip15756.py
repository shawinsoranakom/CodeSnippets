def test_custom_command_with_environment(self):
        """
        alternate: manage.py can execute user commands if settings are provided
        in environment.
        """
        args = ["noargs_command"]
        out, err = self.run_manage(args, "alternate_settings")
        self.assertOutput(
            out,
            "EXECUTE: noargs_command options=[('force_color', False), "
            "('no_color', False), ('pythonpath', None), ('settings', None), "
            "('traceback', False), ('verbosity', 1)]",
        )
        self.assertNoOutput(err)
def test_custom_command_output_color(self):
        """
        alternate: manage.py output syntax color can be deactivated with the
        `--no-color` option.
        """
        args = ["noargs_command", "--no-color", "--settings=alternate_settings"]
        out, err = self.run_manage(args)
        self.assertOutput(
            out,
            "EXECUTE: noargs_command options=[('force_color', False), "
            "('no_color', True), ('pythonpath', None), ('settings', "
            "'alternate_settings'), ('traceback', False), ('verbosity', 1)]",
        )
        self.assertNoOutput(err)
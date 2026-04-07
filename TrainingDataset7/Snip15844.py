def test_suppress_base_options_command_defaults(self):
        args = ["suppress_base_options_command"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertOutput(
            out,
            "EXECUTE:SuppressBaseOptionsCommand options=[('file', None), "
            "('force_color', False), ('no_color', False), "
            "('pythonpath', None), ('settings', None), "
            "('traceback', False), ('verbosity', 1)]",
        )
def test_call_command_option_parsing_non_string_arg(self):
        """
        It should be possible to pass non-string arguments to call_command.
        """
        out = StringIO()
        management.call_command("dance", 1, verbosity=0, stdout=out)
        self.assertIn("You passed 1 as a positional argument.", out.getvalue())
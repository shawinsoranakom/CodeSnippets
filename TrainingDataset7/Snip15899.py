def test_program_name_in_help(self):
        out, err = self.run_test(["-m", "django", "help"])
        self.assertOutput(
            out,
            "Type 'python -m django help <subcommand>' for help on a specific "
            "subcommand.",
        )
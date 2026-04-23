def test_suggest_on_error_defaults_true(self):
        command = BaseCommand()
        parser = command.create_parser("prog_name", "subcommand")
        self.assertTrue(parser.suggest_on_error)
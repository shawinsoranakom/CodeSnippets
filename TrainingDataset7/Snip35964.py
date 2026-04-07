def test_suggest_on_error_explicit_false(self):
        command = BaseCommand()
        parser = command.create_parser(
            "prog_name", "subcommand", suggest_on_error=False
        )
        self.assertFalse(parser.suggest_on_error)
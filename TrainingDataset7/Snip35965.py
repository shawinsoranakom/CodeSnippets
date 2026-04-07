def test_color_enabled_by_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            command = BaseCommand()
            parser = command.create_parser("prog_name", "subcommand")
            self.assertTrue(parser.color)
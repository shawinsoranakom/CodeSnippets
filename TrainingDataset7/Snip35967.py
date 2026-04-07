def test_force_color_does_not_affect_argparse_color(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            command = BaseCommand(force_color=True)
            parser = command.create_parser("prog_name", "subcommand")
            self.assertTrue(parser.color)
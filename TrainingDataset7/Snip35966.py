def test_color_disabled_with_django_colors_nocolor(self):
        with mock.patch.dict(os.environ, {"DJANGO_COLORS": "nocolor"}):
            command = BaseCommand()
            parser = command.create_parser("prog_name", "subcommand")
            self.assertFalse(parser.color)
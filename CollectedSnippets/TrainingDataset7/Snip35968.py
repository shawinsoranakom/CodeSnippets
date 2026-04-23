def test_no_color_flag_disables_color(self):
        with mock.patch.object(sys, "argv", ["manage.py", "mycommand", "--no-color"]):
            command = BaseCommand()
            parser = command.create_parser("manage.py", "mycommand")
            self.assertFalse(parser.color)
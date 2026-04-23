def test_force_color_execute(self):
        out = StringIO()
        err = StringIO()
        with mock.patch.object(sys.stdout, "isatty", lambda: False):
            command = ColorCommand(stdout=out, stderr=err)
            call_command(command, force_color=True)
        self.assertEqual(out.getvalue(), "\x1b[31;1mHello, world!\n\x1b[0m")
        self.assertEqual(err.getvalue(), "\x1b[31;1mHello, world!\n\x1b[0m")
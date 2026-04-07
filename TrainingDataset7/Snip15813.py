def test_command_color(self):
        out = StringIO()
        err = StringIO()
        command = ColorCommand(stdout=out, stderr=err)
        call_command(command)
        if color.supports_color():
            self.assertIn("Hello, world!\n", out.getvalue())
            self.assertIn("Hello, world!\n", err.getvalue())
            self.assertNotEqual(out.getvalue(), "Hello, world!\n")
            self.assertNotEqual(err.getvalue(), "Hello, world!\n")
        else:
            self.assertEqual(out.getvalue(), "Hello, world!\n")
            self.assertEqual(err.getvalue(), "Hello, world!\n")
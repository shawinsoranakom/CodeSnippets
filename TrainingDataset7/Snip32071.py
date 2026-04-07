def test_command_option_globals(self):
        with captured_stdout() as stdout:
            call_command("shell", command=self.script_globals, verbosity=0)
        self.assertEqual(stdout.getvalue().strip(), "True")
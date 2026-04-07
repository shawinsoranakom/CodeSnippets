def test_command_option_inline_function_call(self):
        with captured_stdout() as stdout:
            call_command("shell", command=self.script_with_inline_function, verbosity=0)
        self.assertEqual(stdout.getvalue().strip(), __version__)
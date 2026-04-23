def test_message_with_stdout_zero_object(self):
        class TestCommand(shell.Command):
            def get_auto_imports(self):
                return []

        with captured_stdout() as stdout:
            TestCommand().get_namespace(verbosity=2)

        cases = {
            0: "",
            1: "0 objects imported automatically.",
            2: "0 objects imported automatically.",
        }
        for verbosity, expected in cases.items():
            with self.subTest(verbosity=verbosity):
                with captured_stdout() as stdout:
                    TestCommand().get_namespace(verbosity=verbosity)
                    self.assertEqual(stdout.getvalue().strip(), expected)
def test_override_get_auto_imports_one_error(self):
        class TestCommand(shell.Command):
            def get_auto_imports(self):
                return [
                    "foo",
                ]

        expected = (
            "1 object could not be automatically imported:\n\n  foo\n\n"
            "0 objects imported automatically.\n\n"
        )
        for verbosity, expected in [(0, ""), (1, expected), (2, expected)]:
            with self.subTest(verbosity=verbosity):
                with captured_stdout() as stdout:
                    TestCommand().get_namespace(verbosity=verbosity)
                    self.assertEqual(stdout.getvalue(), expected)
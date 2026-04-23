def test_override_get_auto_imports_many_errors(self):
        class TestCommand(shell.Command):
            def get_auto_imports(self):
                return [
                    "does.not.exist",
                    "doesntexisteither",
                ]

        expected = (
            "2 objects could not be automatically imported:\n\n"
            "  does.not.exist\n"
            "  doesntexisteither\n\n"
            "0 objects imported automatically.\n\n"
        )
        for verbosity, expected in [(0, ""), (1, expected), (2, expected)]:
            with self.subTest(verbosity=verbosity):
                with captured_stdout() as stdout:
                    TestCommand().get_namespace(verbosity=verbosity)
                    self.assertEqual(stdout.getvalue(), expected)
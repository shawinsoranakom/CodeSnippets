def test_override_get_auto_imports(self):
        class TestCommand(shell.Command):
            def get_auto_imports(self):
                return [
                    "model_forms",
                    "shell",
                    "does.not.exist",
                    "doesntexisteither",
                ]

        with captured_stdout() as stdout:
            TestCommand().get_namespace(verbosity=2)

        expected = (
            "2 objects could not be automatically imported:\n\n"
            "  does.not.exist\n"
            "  doesntexisteither\n\n"
            "2 objects imported automatically:\n\n"
            "  import model_forms\n"
            "  import shell\n\n"
        )
        self.assertEqual(stdout.getvalue(), expected)
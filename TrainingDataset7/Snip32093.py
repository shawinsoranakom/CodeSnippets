def test_message_with_stdout_overriden_none_result(self):
        class TestCommand(shell.Command):
            def get_auto_imports(self):
                return None

        for verbosity in [0, 1, 2]:
            with self.subTest(verbosity=verbosity):
                with captured_stdout() as stdout:
                    result = TestCommand().get_namespace(verbosity=verbosity)
                    self.assertEqual(result, {})
                    self.assertEqual(stdout.getvalue().strip(), "")
def test_message_with_stdout_one_object(self):
        class TestCommand(shell.Command):
            def get_auto_imports(self):
                return ["django.db.connection"]

        with captured_stdout() as stdout:
            TestCommand().get_namespace(verbosity=2)

        cases = {
            0: "",
            1: "1 object imported automatically (use -v 2 for details).",
            2: (
                "1 object imported automatically:\n\n"
                "  from django.db import connection"
            ),
        }
        for verbosity, expected in cases.items():
            with self.subTest(verbosity=verbosity):
                with captured_stdout() as stdout:
                    TestCommand().get_namespace(verbosity=verbosity)
                    self.assertEqual(stdout.getvalue().strip(), expected)
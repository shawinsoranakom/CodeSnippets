def test_no_imports_flag(self):
        for verbosity in (0, 1, 2, 3):
            with self.subTest(verbosity=verbosity), captured_stdout() as stdout:
                namespace = shell.Command().get_namespace(
                    verbosity=verbosity, no_imports=True
                )
            self.assertEqual(namespace, {})
            self.assertEqual(stdout.getvalue().strip(), "")
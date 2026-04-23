def test_verbosity_one(self):
        with captured_stdout() as stdout:
            cmd = shell.Command()
            namespace = cmd.get_namespace(verbosity=1)
        self.assertEqual(len(namespace), len(cmd.get_auto_imports()))
        self.assertEqual(
            stdout.getvalue().strip(),
            "12 objects imported automatically (use -v 2 for details).",
        )
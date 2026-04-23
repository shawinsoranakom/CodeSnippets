def test_verbosity_zero(self):
        with captured_stdout() as stdout:
            cmd = shell.Command()
            namespace = cmd.get_namespace(verbosity=0)
        self.assertEqual(len(namespace), len(cmd.get_auto_imports()))
        self.assertEqual(stdout.getvalue().strip(), "")
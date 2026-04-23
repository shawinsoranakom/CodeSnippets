def test_parallel_invalid(self, *mocked_objects):
        with self.assertRaises(SystemExit), captured_stderr() as stderr:
            self.get_parser().parse_args(["--parallel", "unaccepted"])
        msg = "argument --parallel: 'unaccepted' is not an integer or the string 'auto'"
        self.assertIn(msg, stderr.getvalue())
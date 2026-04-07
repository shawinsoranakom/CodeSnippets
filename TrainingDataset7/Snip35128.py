def test_fail(self):
        sys.stderr.write("Write to stderr.")
        sys.stdout.write("Write to stdout.")
        self.assertTrue(False)
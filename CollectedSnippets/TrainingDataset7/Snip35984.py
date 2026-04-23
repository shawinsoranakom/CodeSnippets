def __exit__(self, exc_type, exc_value, traceback):
        self.mocker.stop()
        self.test.assertIn("Formatters failed to launch", self.stderr.getvalue())
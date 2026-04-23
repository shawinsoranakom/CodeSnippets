def setUp(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.stdout, self.stderr = StringIO(), StringIO()
        sys.stdout, sys.stderr = self.stdout, self.stderr
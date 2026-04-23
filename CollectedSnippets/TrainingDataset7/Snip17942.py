def setUp(self):
        self.stdout = StringIO()
        self.addCleanup(self.stdout.close)
        self.stderr = StringIO()
        self.addCleanup(self.stderr.close)
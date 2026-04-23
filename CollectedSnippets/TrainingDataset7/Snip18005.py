def setUp(self):
        self.stdout = StringIO()
        self.addCleanup(self.stdout.close)
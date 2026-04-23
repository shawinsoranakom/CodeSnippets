def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.base = tmp.name
        self.addCleanup(tmp.cleanup)
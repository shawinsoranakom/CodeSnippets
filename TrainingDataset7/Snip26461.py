def setUp(self):
        self.request = self.rf.request()
        self.storage = DummyStorage()
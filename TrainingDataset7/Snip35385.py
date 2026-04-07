def setUp(self):
        self.addCleanup(setattr, self.__class__, "databases", self.databases)
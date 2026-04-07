def setUp(self):
        self.umask = 0o027
        old_umask = os.umask(self.umask)
        self.addCleanup(os.umask, old_umask)
        super().setUp()
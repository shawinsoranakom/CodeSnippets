def setUp(self):
        self.umask = 0o027
        old_umask = os.umask(self.umask)
        self.addCleanup(os.umask, old_umask)
        self.storage_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.storage_dir)
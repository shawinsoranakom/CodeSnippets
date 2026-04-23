def setUp(self):
        self.testdir = os.path.join(os.path.dirname(__file__), "archives")
        old_cwd = os.getcwd()
        os.chdir(self.testdir)
        self.addCleanup(os.chdir, old_cwd)
def setUp(self):
        super().setUp()
        self._temp_dir = temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(temp_dir, "test"))
        self.addCleanup(shutil.rmtree, temp_dir)
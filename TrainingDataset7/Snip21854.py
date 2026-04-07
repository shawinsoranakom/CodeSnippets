def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.storage = self.storage_class(
            location=self.temp_dir, base_url="/test_media_url/"
        )
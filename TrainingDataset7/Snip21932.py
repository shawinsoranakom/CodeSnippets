def setUp(self):
        storage_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, storage_dir)
        self.storage = FileSystemStorage(storage_dir)
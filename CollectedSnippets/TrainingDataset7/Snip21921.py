def setUp(self):
        self.storage_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.storage_dir)
        self.storage = FileSystemStorage(self.storage_dir)
        self.thread = threading.Thread(target=self.save_file, args=["conflict"])
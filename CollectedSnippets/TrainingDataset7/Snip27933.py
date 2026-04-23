def setUp(self):
        """
        Creates a pristine temp directory (or deletes and recreates if it
        already exists) that the model uses as its storage directory.

        Sets up two ImageFile instances for use in tests.
        """
        if os.path.exists(temp_storage_dir):
            shutil.rmtree(temp_storage_dir)
        os.mkdir(temp_storage_dir)
        self.addCleanup(shutil.rmtree, temp_storage_dir)
        file_path1 = os.path.join(os.path.dirname(__file__), "4x8.png")
        self.file1 = self.File(open(file_path1, "rb"), name="4x8.png")
        self.addCleanup(self.file1.close)
        file_path2 = os.path.join(os.path.dirname(__file__), "8x4.png")
        self.file2 = self.File(open(file_path2, "rb"), name="8x4.png")
        self.addCleanup(self.file2.close)
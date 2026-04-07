def setUp(self):
        super().setUp()
        self.finder = finders.FileSystemFinder()
        test_file_path = os.path.join(
            TEST_ROOT, "project", "documents", "test", "file.txt"
        )
        self.find_first = (os.path.join("test", "file.txt"), test_file_path)
        self.find_all = (os.path.join("test", "file.txt"), [test_file_path])
def setUp(self):
        super().setUp()
        self.finder = finders.AppDirectoriesFinder()
        test_file_path = os.path.join(
            TEST_ROOT, "apps", "test", "static", "test", "file1.txt"
        )
        self.find_first = (os.path.join("test", "file1.txt"), test_file_path)
        self.find_all = (os.path.join("test", "file1.txt"), [test_file_path])
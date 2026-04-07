def test_size_not_exceeded(self):
        with self.settings(DATA_UPLOAD_MAX_MEMORY_SIZE=11):
            self.request._load_post_and_files()
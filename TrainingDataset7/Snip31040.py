def test_no_limit(self):
        with self.settings(DATA_UPLOAD_MAX_MEMORY_SIZE=None):
            self.request._load_post_and_files()
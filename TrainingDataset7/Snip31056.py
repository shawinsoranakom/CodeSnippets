def test_no_limit(self):
        with self.settings(DATA_UPLOAD_MAX_NUMBER_FILES=None):
            self.request._load_post_and_files()
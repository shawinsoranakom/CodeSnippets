def test_number_not_exceeded(self):
        with self.settings(DATA_UPLOAD_MAX_NUMBER_FILES=2):
            self.request._load_post_and_files()
def test_number_not_exceeded(self):
        with self.settings(DATA_UPLOAD_MAX_NUMBER_FIELDS=3):
            self.request._load_post_and_files()
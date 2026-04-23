def test_number_exceeded(self):
        with self.settings(DATA_UPLOAD_MAX_NUMBER_FILES=1):
            with self.assertRaisesMessage(TooManyFilesSent, TOO_MANY_FILES_MSG):
                self.request._load_post_and_files()
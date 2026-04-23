def test_number_exceeded(self):
        with self.settings(DATA_UPLOAD_MAX_NUMBER_FIELDS=2):
            with self.assertRaisesMessage(TooManyFieldsSent, TOO_MANY_FIELDS_MSG):
                self.request._load_post_and_files()
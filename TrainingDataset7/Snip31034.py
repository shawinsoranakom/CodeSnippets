def test_size_exceeded(self):
        with self.settings(DATA_UPLOAD_MAX_MEMORY_SIZE=12):
            with self.assertRaisesMessage(RequestDataTooBig, TOO_MUCH_DATA_MSG):
                self.request._load_post_and_files()
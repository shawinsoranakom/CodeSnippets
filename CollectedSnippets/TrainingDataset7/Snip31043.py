def test_data_upload_max_memory_size_exceeded(self):
        with self.settings(DATA_UPLOAD_MAX_MEMORY_SIZE=2):
            with self.assertRaisesMessage(RequestDataTooBig, TOO_MUCH_DATA_MSG):
                self.request.body
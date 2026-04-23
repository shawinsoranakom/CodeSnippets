def test_no_limit(self):
        with self.settings(DATA_UPLOAD_MAX_MEMORY_SIZE=None):
            self.request.body
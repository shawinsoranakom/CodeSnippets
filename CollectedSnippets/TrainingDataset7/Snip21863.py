def test_file_get_created_time_timezone(self):
        self._test_file_time_getter(self.storage.get_created_time)
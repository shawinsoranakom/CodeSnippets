def tearDown(self):
        super().tearDown()
        settings.SESSION_FILE_PATH = self.original_session_file_path
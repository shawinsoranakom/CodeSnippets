def setUp(self):
        # Do file session tests in an isolated directory, and kill it after
        # we're done.
        self.original_session_file_path = settings.SESSION_FILE_PATH
        self.temp_session_store = settings.SESSION_FILE_PATH = self.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_session_store)
        # Reset the file session backend's internal caches
        if hasattr(self.backend, "_storage_path"):
            del self.backend._storage_path
        super().setUp()
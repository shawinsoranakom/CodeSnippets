def tearDown(self):
        # Clear hashed files to avoid side effects among tests.
        storage.staticfiles_storage.hashed_files.clear()
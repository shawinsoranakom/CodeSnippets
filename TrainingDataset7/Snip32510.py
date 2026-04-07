def setUp(self):
        storage.staticfiles_storage.hashed_files.clear()  # avoid cache interference
        super().setUp()
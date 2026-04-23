def setUp(self):
        self.temp_storage_location = tempfile.mkdtemp(
            suffix="filefield_callable_storage"
        )
        self.addCleanup(shutil.rmtree, self.temp_storage_location)
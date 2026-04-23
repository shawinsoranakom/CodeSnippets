def test_callable_function_storage_file_field(self):
        storage = FileSystemStorage(location=self.temp_storage_location)

        def get_storage():
            return storage

        obj = FileField(storage=get_storage)
        self.assertEqual(obj.storage, storage)
        self.assertEqual(obj.storage.location, storage.location)
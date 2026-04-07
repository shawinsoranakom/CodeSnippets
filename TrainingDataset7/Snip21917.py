def test_callable_storage_file_field_in_model(self):
        obj = Storage()
        self.assertEqual(obj.storage_callable.storage, temp_storage)
        self.assertEqual(obj.storage_callable.storage.location, temp_storage_location)
        self.assertIsInstance(obj.storage_callable_class.storage, BaseStorage)
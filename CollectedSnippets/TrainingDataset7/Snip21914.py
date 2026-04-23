def test_file_field_storage_none_uses_default_storage(self):
        self.assertEqual(FileField().storage, default_storage)
def test_create_file_field_from_another_file_field_in_memory_storage(self):
        f = ContentFile("content", "file.txt")
        obj = Storage.objects.create(storage_callable_default=f)
        new_obj = Storage.objects.create(
            storage_callable_default=obj.storage_callable_default.file
        )
        storage = callable_default_storage()
        with storage.open(new_obj.storage_callable_default.name) as f:
            self.assertEqual(f.read(), b"content")
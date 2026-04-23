def test_callable_class_storage_file_field(self):
        class GetStorage(FileSystemStorage):
            pass

        obj = FileField(storage=GetStorage)
        self.assertIsInstance(obj.storage, BaseStorage)
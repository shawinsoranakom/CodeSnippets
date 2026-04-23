def test_file_upload_permissions(self):
        self.storage = FileSystemStorage(self.storage_dir)
        name = self.storage.save("the_file", ContentFile("data"))
        actual_mode = os.stat(self.storage.path(name))[0] & 0o777
        self.assertEqual(actual_mode, 0o654)
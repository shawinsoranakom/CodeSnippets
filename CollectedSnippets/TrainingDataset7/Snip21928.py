def test_file_upload_directory_default_permissions(self):
        self.storage = FileSystemStorage(self.storage_dir)
        name = self.storage.save("the_directory/subdir/the_file", ContentFile("data"))
        file_path = Path(self.storage.path(name))
        expected_mode = 0o777 & ~self.umask
        self.assertEqual(file_path.parent.stat().st_mode & 0o777, expected_mode)
        self.assertEqual(file_path.parent.parent.stat().st_mode & 0o777, expected_mode)
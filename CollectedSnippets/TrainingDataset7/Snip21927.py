def test_file_upload_directory_permissions(self):
        self.storage = FileSystemStorage(self.storage_dir)
        name = self.storage.save("the_directory/subdir/the_file", ContentFile("data"))
        file_path = Path(self.storage.path(name))
        self.assertEqual(file_path.parent.stat().st_mode & 0o777, 0o765)
        self.assertEqual(file_path.parent.parent.stat().st_mode & 0o777, 0o765)
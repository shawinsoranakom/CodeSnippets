def test_file_storage_preserves_filename_case(self):
        """The storage backend should preserve case of filenames."""
        # Create a storage backend associated with the mixed case name
        # directory.
        temp_dir2 = tempfile.mkdtemp(suffix="aBc")
        self.addCleanup(shutil.rmtree, temp_dir2)
        other_temp_storage = self.storage_class(location=temp_dir2)
        # Ask that storage backend to store a file with a mixed case filename.
        mixed_case = "CaSe_SeNsItIvE"
        file = other_temp_storage.open(mixed_case, "w")
        file.write("storage contents")
        file.close()
        self.assertEqual(
            os.path.join(temp_dir2, mixed_case),
            other_temp_storage.path(mixed_case),
        )
        other_temp_storage.delete(mixed_case)
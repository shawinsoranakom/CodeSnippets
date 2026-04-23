def test_file_save_broken_symlink(self):
        """A new path is created on save when a broken symlink is supplied."""
        nonexistent_file_path = os.path.join(self.temp_dir, "nonexistent.txt")
        broken_symlink_file_name = "symlink.txt"
        broken_symlink_path = os.path.join(self.temp_dir, broken_symlink_file_name)
        os.symlink(nonexistent_file_path, broken_symlink_path)
        f = ContentFile("some content")
        f_name = self.storage.save(broken_symlink_file_name, f)
        self.assertIs(os.path.exists(os.path.join(self.temp_dir, f_name)), True)
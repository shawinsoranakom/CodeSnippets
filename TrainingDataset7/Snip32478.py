def test_clear_broken_symlink(self):
        """
        With ``--clear``, broken symbolic links are deleted.
        """
        nonexistent_file_path = os.path.join(settings.STATIC_ROOT, "nonexistent.txt")
        broken_symlink_path = os.path.join(settings.STATIC_ROOT, "symlink.txt")
        os.symlink(nonexistent_file_path, broken_symlink_path)
        self.run_collectstatic(clear=True)
        self.assertFalse(os.path.lexists(broken_symlink_path))
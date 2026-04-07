def test_no_files_created(self):
        """
        Make sure no files were create in the destination directory.
        """
        self.assertEqual(os.listdir(settings.STATIC_ROOT), [])
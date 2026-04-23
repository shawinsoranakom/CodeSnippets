def test_reject_null_files(self):
        """MediaFileManager.add raises a TypeError if it's passed None."""
        with self.assertRaises(TypeError):
            self.media_file_manager.add(None, "media/any", random_coordinates())
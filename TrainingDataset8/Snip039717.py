def test_add_file_already_exists_different_coord(self):
        """Adding a file that already exists, but with different coordinates,
        results in just a single file in the manager.
        """
        sample = IMAGE_FIXTURES["png"]

        coord = random_coordinates()
        self.media_file_manager.add(sample["content"], sample["mimetype"], coord)
        file_id = _calculate_file_id(sample["content"], sample["mimetype"])
        self.assertTrue(file_id in self.media_file_manager._file_metadata)

        coord = random_coordinates()
        self.media_file_manager.add(sample["content"], sample["mimetype"], coord)
        self.assertTrue(file_id in self.media_file_manager._file_metadata)

        # There should only be 1 file in MFM.
        self.assertEqual(len(self.media_file_manager._file_metadata), 1)

        # There should only be 1 session with registered files.
        self.assertEqual(len(self.media_file_manager._files_by_session_and_coord), 1)
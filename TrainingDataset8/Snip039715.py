def test_add_files_same_coord(self):
        """We can add multiple files that share the same coordinate."""
        coord = random_coordinates()

        for sample in ALL_FIXTURES.values():
            self.media_file_manager.add(sample["content"], sample["mimetype"], coord)

        # There should be 6 files in MFM.
        self.assertEqual(len(self.media_file_manager._file_metadata), len(ALL_FIXTURES))

        # There should only be 1 session with registered files.
        self.assertEqual(len(self.media_file_manager._files_by_session_and_coord), 1)

        # There should only be 1 coord in that session.
        self.assertEqual(
            len(self.media_file_manager._files_by_session_and_coord["mock_session_id"]),
            1,
        )

        self.media_file_manager.clear_session_refs()
        self.media_file_manager.remove_orphaned_files()

        # There should be only 0 file in MFM.
        self.assertEqual(len(self.media_file_manager._file_metadata), 0)

        # There should only be 0 session with registered files.
        self.assertEqual(len(self.media_file_manager._files_by_session_and_coord), 0)
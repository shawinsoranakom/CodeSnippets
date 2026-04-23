def test_add_file_by_name(self):
        """Test that we can add files by filename."""
        storage_load_spy = MagicMock(side_effect=self.storage.load_and_get_id)
        self.storage.load_and_get_id = storage_load_spy

        self.media_file_manager.add(
            "mock/file/path.png", "image/png", random_coordinates()
        )

        # We should have a single file in the MFM.
        self.assertEqual(len(self.media_file_manager._file_metadata), 1)

        # And it should be registered to our session
        self.assertEqual(
            len(self.media_file_manager._files_by_session_and_coord["mock_session"]), 1
        )

        # Ensure MediaFileStorage.load_and_get_id was called as expected.
        storage_load_spy.assert_called_once_with(
            "mock/file/path.png", "image/png", MediaFileKind.MEDIA, None
        )
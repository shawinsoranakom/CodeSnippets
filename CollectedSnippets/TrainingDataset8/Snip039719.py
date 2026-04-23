def test_remove_orphaned_files_multiple_sessions(self, mock_get_session_id):
        """clear_session_refs/remove_orphaned_files behaves correctly when multiple
        sessions are referencing some of the same files.
        """
        storage_delete_spy = MagicMock(side_effect=self.storage.delete_file)
        self.storage.delete_file = storage_delete_spy

        # Have two sessions add the same set of files
        for session_id in ("mock_session_1", "mock_session_2"):
            mock_get_session_id.return_value = session_id
            for sample in VIDEO_FIXTURES.values():
                coord = random_coordinates()
                self.media_file_manager.add(
                    sample["content"], sample["mimetype"], coord
                )

        self.assertEqual(
            len(self.media_file_manager._file_metadata), len(VIDEO_FIXTURES)
        )

        file_ids = list(self.media_file_manager._file_metadata.keys())

        # Remove session1's references
        mock_get_session_id.return_value = "mock_session_1"
        self.media_file_manager.clear_session_refs()
        self.media_file_manager.remove_orphaned_files()

        # The files are all still referenced by session_2
        self.assertEqual(
            len(self.media_file_manager._file_metadata), len(VIDEO_FIXTURES)
        )

        # MediaFileStorage.delete_file should not have been called yet...
        storage_delete_spy.assert_not_called()

        # Remove session2's references, but don't call "remove_orphaned_files" yet...
        mock_get_session_id.return_value = "mock_session_2"
        self.media_file_manager.clear_session_refs()

        # The files still exist, because they've only been de-referenced and not
        # removed.
        self.assertEqual(
            len(self.media_file_manager._file_metadata), len(VIDEO_FIXTURES)
        )

        # MediaFileStorage.delete_file should not have been called yet...
        storage_delete_spy.assert_not_called()

        # After a final call to remove_orphaned_files, the files should be gone.
        self.media_file_manager.remove_orphaned_files()
        self.assertEqual(len(self.media_file_manager._file_metadata), 0)

        # MediaFileStorage.delete_file should have been called once for each
        # file.
        storage_delete_spy.assert_has_calls(
            [call(file_id) for file_id in file_ids], any_order=True
        )
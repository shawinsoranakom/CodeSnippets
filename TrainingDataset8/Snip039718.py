def test_remove_orphaned_files_in_empty_manager(self):
        """Calling clear_session_refs/remove_orphaned_files in an empty manager
        is a no-op.
        """
        storage_delete_spy = MagicMock(side_effect=self.storage.delete_file)
        self.storage.delete_file = storage_delete_spy

        self.assertEqual(len(self.media_file_manager._file_metadata), 0)
        self.assertEqual(len(self.media_file_manager._files_by_session_and_coord), 0)

        self.media_file_manager.clear_session_refs()
        self.media_file_manager.remove_orphaned_files()

        self.assertEqual(len(self.media_file_manager._file_metadata), 0)
        self.assertEqual(len(self.media_file_manager._files_by_session_and_coord), 0)

        # MediaFileStorage.delete_file should not have been called, because
        # no files were actually deleted.
        storage_delete_spy.assert_not_called()
def test_add_binary_files(self):
        """Test that we can add binary files to the manager."""
        storage_load_spy = MagicMock(side_effect=self.storage.load_and_get_id)
        self.storage.load_and_get_id = storage_load_spy

        sample_coords = set()
        while len(sample_coords) < len(ALL_FIXTURES):
            sample_coords.add(random_coordinates())

        for sample in ALL_FIXTURES.values():
            content = sample["content"]
            self.assertIsInstance(content, bytes)
            mimetype = sample["mimetype"]
            media_file = self._add_file_and_get_object(
                content, mimetype, sample_coords.pop()
            )
            self.assertIsNotNone(media_file)

            # Ensure MediaFileStorage.load_and_get_id was called as expected.
            storage_load_spy.assert_called_once_with(
                content, mimetype, MediaFileKind.MEDIA, None
            )
            storage_load_spy.reset_mock()

        # There should be as many files in MFM as we added.
        self.assertEqual(len(self.media_file_manager._file_metadata), len(ALL_FIXTURES))

        # There should only be 1 session with registered files.
        self.assertEqual(len(self.media_file_manager._files_by_session_and_coord), 1)
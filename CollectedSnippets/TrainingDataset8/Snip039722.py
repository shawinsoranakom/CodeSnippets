def test_clear_files_multiple_threads(self):
        """We can safely clear session refs and remove orphaned files
        from multiple threads simultaneously.
        """
        # Add a bunch of files
        for sample in ALL_FIXTURES.values():
            self.media_file_manager.add(
                sample["content"], sample["mimetype"], random_coordinates()
            )
        self.assertEqual(len(ALL_FIXTURES), len(self.media_file_manager._file_metadata))

        # Remove those files from multiple threads
        def remove_files(_: int) -> None:
            self.media_file_manager.clear_session_refs("mock_session_id")
            self.media_file_manager.remove_orphaned_files()

        call_on_threads(remove_files, num_threads=self.NUM_THREADS)

        # Our files should be gone!
        self.assertEqual(0, len(self.media_file_manager._file_metadata))
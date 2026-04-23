def test_cache_stats(self):
        """Test our CacheStatsProvider implementation."""
        self.assertEqual(0, len(self.storage.get_stats()))

        # Add several files to storage. We'll unique-ify them by filename.
        mock_data = b"some random mock binary data"
        num_files = 5
        for ii in range(num_files):
            self.storage.load_and_get_id(
                mock_data,
                mimetype="video/mp4",
                kind=MediaFileKind.MEDIA,
                filename=f"{ii}.mp4",
            )

        stats = self.storage.get_stats()
        self.assertEqual(num_files, len(stats))
        self.assertEqual("st_memory_media_file_storage", stats[0].category_name)
        self.assertEqual(
            len(mock_data) * num_files, sum(stat.byte_length for stat in stats)
        )

        # Remove files, and ensure our cache doesn't report they still exist
        for file_id in list(self.storage._files_by_id.keys()):
            self.storage.delete_file(file_id)

        self.assertEqual(0, len(self.storage.get_stats()))
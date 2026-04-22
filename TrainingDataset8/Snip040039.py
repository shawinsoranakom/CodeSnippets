def test_cache_stats_provider(self):
        """Test CacheStatsProvider implementation."""

        # Test empty manager
        self.assertEqual([], self.mgr.get_stats())

        # Test manager with files
        self.mgr.add_file("session1", "widget1", FILE_1)
        self.mgr.add_file("session1", "widget2", FILE_2)

        expected = [
            CacheStat(
                category_name="UploadedFileManager",
                cache_name="",
                byte_length=len(FILE_1.data),
            ),
            CacheStat(
                category_name="UploadedFileManager",
                cache_name="",
                byte_length=len(FILE_2.data),
            ),
        ]
        self.assertEqual(expected, self.mgr.get_stats())
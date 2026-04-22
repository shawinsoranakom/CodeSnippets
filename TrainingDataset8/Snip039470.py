def test_cache_stats_provider(self):
        """Test ForwardMsgCache's CacheStatsProvider implementation."""
        cache = ForwardMsgCache()
        session = _create_mock_session()

        # Test empty cache
        self.assertEqual([], cache.get_stats())

        msg1 = _create_dataframe_msg([1, 2, 3])
        populate_hash_if_needed(msg1)
        cache.add_message(msg1, session, 0)

        msg2 = _create_dataframe_msg([5, 4, 3, 2, 1, 0])
        populate_hash_if_needed(msg2)
        cache.add_message(msg2, session, 0)

        # Test cache with messages
        expected = [
            CacheStat(
                category_name="ForwardMessageCache",
                cache_name="",
                byte_length=msg1.ByteSize(),
            ),
            CacheStat(
                category_name="ForwardMessageCache",
                cache_name="",
                byte_length=msg2.ByteSize(),
            ),
        ]
        self.assertEqual(set(expected), set(cache.get_stats()))
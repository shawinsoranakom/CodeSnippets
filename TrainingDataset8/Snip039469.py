def test_message_expiration(self):
        """Test MessageCache's expiration logic"""
        config._set_option("global.maxCachedMessageAge", 1, "test")

        cache = ForwardMsgCache()
        session1 = _create_mock_session()
        runcount1 = 0

        msg = _create_dataframe_msg([1, 2, 3])
        msg_hash = populate_hash_if_needed(msg)

        cache.add_message(msg, session1, runcount1)

        # Increment session1's run_count. This should not resolve in expiry.
        runcount1 += 1
        self.assertTrue(cache.has_message_reference(msg, session1, runcount1))

        # Increment again. The message will now be expired for session1,
        # though it won't have actually been removed yet.
        runcount1 += 1
        self.assertFalse(cache.has_message_reference(msg, session1, runcount1))
        self.assertIsNotNone(cache.get_message(msg_hash))

        # Add another reference to the message
        session2 = _create_mock_session()
        runcount2 = 0
        cache.add_message(msg, session2, runcount2)

        # Remove session1's expired entries. This should not remove the
        # entry from the cache, because session2 still has a reference to it.
        cache.remove_expired_session_entries(session1, runcount1)
        self.assertFalse(cache.has_message_reference(msg, session1, runcount1))
        self.assertTrue(cache.has_message_reference(msg, session2, runcount2))

        # Expire session2's reference. The message should no longer be
        # in the cache at all.
        runcount2 += 2
        cache.remove_expired_session_entries(session2, runcount2)
        self.assertIsNone(cache.get_message(msg_hash))
def test_get_message(self):
        """Test MessageCache.get_message"""
        cache = ForwardMsgCache()
        session = _create_mock_session()
        msg = _create_dataframe_msg([1, 2, 3])

        msg_hash = populate_hash_if_needed(msg)

        cache.add_message(msg, session, 0)
        self.assertEqual(msg, cache.get_message(msg_hash))
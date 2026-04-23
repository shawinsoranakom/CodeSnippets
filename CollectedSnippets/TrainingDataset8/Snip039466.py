def test_add_message(self):
        """Test MessageCache.add_message and has_message_reference"""
        cache = ForwardMsgCache()
        session = _create_mock_session()
        msg = _create_dataframe_msg([1, 2, 3])
        cache.add_message(msg, session, 0)

        self.assertTrue(cache.has_message_reference(msg, session, 0))
        self.assertFalse(cache.has_message_reference(msg, _create_mock_session(), 0))
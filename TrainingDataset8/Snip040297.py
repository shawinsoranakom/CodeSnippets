def test_message_cache(self):
        # Create a new ForwardMsg and cache it
        msg = create_dataframe_msg([1, 2, 3])
        msg_hash = populate_hash_if_needed(msg)
        self._cache.add_message(msg, MagicMock(), 0)

        # Cache hit
        response = self.fetch("/message?hash=%s" % msg_hash)
        self.assertEqual(200, response.code)
        self.assertEqual(serialize_forward_msg(msg), response.body)

        # Cache misses
        self.assertEqual(404, self.fetch("/message").code)
        self.assertEqual(404, self.fetch("/message?id=non_existent").code)
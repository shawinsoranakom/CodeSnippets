def test_cached_garbaged_collected(self):
        """
        Make sure signal caching sender receivers don't prevent garbage
        collection of senders.
        """

        class sender:
            pass

        wref = weakref.ref(sender)
        d_signal.connect(receiver_1_arg)
        d_signal.send(sender, val="garbage")
        del sender
        garbage_collect()
        try:
            self.assertIsNone(wref())
        finally:
            # Disconnect after reference check since it flushes the tested
            # cache.
            d_signal.disconnect(receiver_1_arg)
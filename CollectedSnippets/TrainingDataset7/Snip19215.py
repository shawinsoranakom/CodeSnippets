def test_close(self):
        self.assertFalse(cache.closed)
        signals.request_finished.send(self.__class__)
        self.assertTrue(cache.closed)
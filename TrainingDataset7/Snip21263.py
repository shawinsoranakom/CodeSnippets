def assertTestIsClean(self, signal):
        """Assert that everything has been cleaned up automatically"""
        # Note that dead weakref cleanup happens as side effect of using
        # the signal's receivers through the signals API. So, first do a
        # call to an API method to force cleanup.
        self.assertFalse(signal.has_listeners())
        self.assertEqual(signal.receivers, [])
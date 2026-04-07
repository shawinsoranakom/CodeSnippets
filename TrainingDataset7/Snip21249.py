def test_removedafternextversionwarning_pending(self):
        self.assertTrue(
            issubclass(RemovedAfterNextVersionWarning, PendingDeprecationWarning)
        )
def test_pre_callback(self):
        def pre_hook():
            pass

        transaction.on_commit(pre_hook, using="default")
        with self.captureOnCommitCallbacks() as callbacks:
            self.enqueue_callback()

        self.assertEqual(len(callbacks), 1)
        self.assertNotEqual(callbacks[0], pre_hook)
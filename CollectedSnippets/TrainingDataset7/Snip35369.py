def test_different_using(self):
        with self.captureOnCommitCallbacks(using="default") as callbacks:
            self.enqueue_callback(using="other")

        self.assertEqual(callbacks, [])
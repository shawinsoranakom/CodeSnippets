def test_using(self):
        with self.captureOnCommitCallbacks(using="other") as callbacks:
            self.enqueue_callback(using="other")

        self.assertEqual(len(callbacks), 1)
        self.assertIs(self.callback_called, False)
        callbacks[0]()
        self.assertIs(self.callback_called, True)
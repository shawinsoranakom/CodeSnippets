def test_no_arguments(self):
        with self.captureOnCommitCallbacks() as callbacks:
            self.enqueue_callback()

        self.assertEqual(len(callbacks), 1)
        self.assertIs(self.callback_called, False)
        callbacks[0]()
        self.assertIs(self.callback_called, True)
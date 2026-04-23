def test_execute(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            self.enqueue_callback()

        self.assertEqual(len(callbacks), 1)
        self.assertIs(self.callback_called, True)
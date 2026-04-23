def test_execute_recursive(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            transaction.on_commit(self.enqueue_callback)

        self.assertEqual(len(callbacks), 2)
        self.assertIs(self.callback_called, True)
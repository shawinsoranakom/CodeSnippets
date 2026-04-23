def test_execute_robust_with_callback_as_partial(self):
        class MyException(Exception):
            pass

        def hook():
            self.callback_called = True
            raise MyException("robust callback")

        hook_partial = partial(hook)

        with self.assertLogs("django.test", "ERROR") as cm:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                transaction.on_commit(hook_partial, robust=True)

        self.assertEqual(len(callbacks), 1)
        self.assertIs(self.callback_called, True)

        log_record = cm.records[0]
        self.assertEqual(
            log_record.getMessage(),
            f"Error calling {hook_partial} in on_commit() (robust callback).",
        )
        self.assertIsNotNone(log_record.exc_info)
        raised_exception = log_record.exc_info[1]
        self.assertIsInstance(raised_exception, MyException)
        self.assertEqual(str(raised_exception), "robust callback")
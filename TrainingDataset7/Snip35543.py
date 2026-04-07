def test_robust_transaction_with_callback_as_partial(self):
        def robust_callback():
            raise ForcedError("robust callback")

        robust_callback_partial = partial(robust_callback)

        with self.assertLogs("django.db.backends", "ERROR") as cm:
            with transaction.atomic():
                transaction.on_commit(robust_callback_partial, robust=True)
                self.do(1)

        self.assertDone([1])
        log_record = cm.records[0]
        self.assertEqual(
            log_record.getMessage(),
            f"Error calling {robust_callback_partial} in on_commit() during "
            "transaction (robust callback).",
        )
        self.assertIsNotNone(log_record.exc_info)
        raised_exception = log_record.exc_info[1]
        self.assertIsInstance(raised_exception, ForcedError)
        self.assertEqual(str(raised_exception), "robust callback")
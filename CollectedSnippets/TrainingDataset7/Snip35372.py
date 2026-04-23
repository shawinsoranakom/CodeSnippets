def test_with_rolled_back_savepoint(self):
        with self.captureOnCommitCallbacks() as callbacks:
            try:
                with transaction.atomic():
                    self.enqueue_callback()
                    raise IntegrityError
            except IntegrityError:
                # Inner transaction.atomic() has been rolled back.
                pass

        self.assertEqual(callbacks, [])
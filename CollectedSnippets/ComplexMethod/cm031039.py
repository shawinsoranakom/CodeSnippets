def test_cancel_futures(self):
        assert self.worker_count <= 5, "test needs few workers"
        fs = [self.executor.submit(time.sleep, .1) for _ in range(50)]
        self.executor.shutdown(cancel_futures=True)
        # We can't guarantee the exact number of cancellations, but we can
        # guarantee that *some* were cancelled. With few workers, many of
        # the submitted futures should have been cancelled.
        cancelled = [fut for fut in fs if fut.cancelled()]
        self.assertGreater(len(cancelled), 20)

        # Ensure the other futures were able to finish.
        # Use "not fut.cancelled()" instead of "fut.done()" to include futures
        # that may have been left in a pending state.
        others = [fut for fut in fs if not fut.cancelled()]
        for fut in others:
            self.assertTrue(fut.done(), msg=f"{fut._state=}")
            self.assertIsNone(fut.exception())

        # Similar to the number of cancelled futures, we can't guarantee the
        # exact number that completed. But, we can guarantee that at least
        # one finished.
        self.assertGreater(len(others), 0)
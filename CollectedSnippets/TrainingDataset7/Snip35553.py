def test_hooks_cleared_after_successful_commit(self):
        with transaction.atomic():
            self.do(1)
        with transaction.atomic():
            self.do(2)

        self.assertDone([1, 2])
def test_hooks_cleared_after_rollback(self):
        try:
            with transaction.atomic():
                self.do(1)
                raise ForcedError()
        except ForcedError:
            pass

        with transaction.atomic():
            self.do(2)

        self.assertDone([2])
def test_no_hooks_run_from_failed_transaction(self):
        """If outer transaction fails, no hooks from within it run."""
        try:
            with transaction.atomic():
                with transaction.atomic():
                    self.do(1)
                raise ForcedError()
        except ForcedError:
            pass

        self.assertDone([])
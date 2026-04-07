def test_does_not_execute_if_transaction_rolled_back(self):
        try:
            with transaction.atomic():
                self.do(1)
                raise ForcedError()
        except ForcedError:
            pass

        self.assertDone([])
def test_delays_execution_until_after_transaction_commit(self):
        with transaction.atomic():
            self.do(1)
            self.assertNotified([])
        self.assertDone([1])
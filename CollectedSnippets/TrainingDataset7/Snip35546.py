def test_executes_only_after_final_transaction_committed(self):
        with transaction.atomic():
            with transaction.atomic():
                self.do(1)
                self.assertNotified([])
            self.assertNotified([])
        self.assertDone([1])
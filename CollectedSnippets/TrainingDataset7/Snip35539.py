def test_executes_immediately_if_no_transaction(self):
        self.do(1)
        self.assertDone([1])
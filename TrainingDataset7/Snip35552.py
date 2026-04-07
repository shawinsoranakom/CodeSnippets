def test_runs_hooks_in_order_registered(self):
        with transaction.atomic():
            self.do(1)
            with transaction.atomic():
                self.do(2)
            self.do(3)

        self.assertDone([1, 2, 3])
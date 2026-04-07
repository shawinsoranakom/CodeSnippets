def test_defer(self):
        instance = CashModel.objects.defer("cash").get()
        self.assertIsInstance(instance.cash, Cash)
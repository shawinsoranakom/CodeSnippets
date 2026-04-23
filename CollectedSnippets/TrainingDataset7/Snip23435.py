def test_simple_load(self):
        instance = CashModel.objects.get()
        self.assertIsInstance(instance.cash, Cash)
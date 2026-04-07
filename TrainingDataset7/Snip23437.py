def test_values(self):
        values = CashModel.objects.values("cash")
        self.assertIsInstance(values[0]["cash"], Cash)
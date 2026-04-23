def test_values_list(self):
        values_list = CashModel.objects.values_list("cash", flat=True)
        self.assertIsInstance(values_list[0], Cash)
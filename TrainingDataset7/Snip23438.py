def test_aggregation(self):
        maximum = CashModel.objects.aggregate(m=Max("cash"))["m"]
        self.assertIsInstance(maximum, Cash)
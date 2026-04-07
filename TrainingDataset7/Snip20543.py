def test_decimal_with_precision(self):
        DecimalModel.objects.create(n1=Decimal("-5.75"), n2=Pi())
        obj = DecimalModel.objects.annotate(
            n1_round=Round("n1", 1),
            n2_round=Round("n2", 5),
        ).first()
        self.assertIsInstance(obj.n1_round, Decimal)
        self.assertIsInstance(obj.n2_round, Decimal)
        self.assertAlmostEqual(obj.n1_round, obj.n1, places=1)
        self.assertAlmostEqual(obj.n2_round, obj.n2, places=5)
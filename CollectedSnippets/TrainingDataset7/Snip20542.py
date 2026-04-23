def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-12.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(
            n1_round=Round("n1"), n2_round=Round("n2")
        ).first()
        self.assertIsInstance(obj.n1_round, Decimal)
        self.assertIsInstance(obj.n2_round, Decimal)
        self.assertAlmostEqual(obj.n1_round, obj.n1, places=0)
        self.assertAlmostEqual(obj.n2_round, obj.n2, places=0)
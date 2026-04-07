def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("12.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(
            n1_ceil=Ceil("n1"), n2_ceil=Ceil("n2")
        ).first()
        self.assertIsInstance(obj.n1_ceil, Decimal)
        self.assertIsInstance(obj.n2_ceil, Decimal)
        self.assertEqual(obj.n1_ceil, Decimal(math.ceil(obj.n1)))
        self.assertEqual(obj.n2_ceil, Decimal(math.ceil(obj.n2)))
def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("0.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(
            n1_asin=ASin("n1"), n2_asin=ASin("n2")
        ).first()
        self.assertIsInstance(obj.n1_asin, Decimal)
        self.assertIsInstance(obj.n2_asin, Decimal)
        self.assertAlmostEqual(obj.n1_asin, Decimal(math.asin(obj.n1)))
        self.assertAlmostEqual(obj.n2_asin, Decimal(math.asin(obj.n2)))
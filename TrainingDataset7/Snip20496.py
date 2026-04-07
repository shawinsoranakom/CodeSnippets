def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-12.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(n1_cot=Cot("n1"), n2_cot=Cot("n2")).first()
        self.assertIsInstance(obj.n1_cot, Decimal)
        self.assertIsInstance(obj.n2_cot, Decimal)
        self.assertAlmostEqual(obj.n1_cot, Decimal(1 / math.tan(obj.n1)))
        self.assertAlmostEqual(obj.n2_cot, Decimal(1 / math.tan(obj.n2)))
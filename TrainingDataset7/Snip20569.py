def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-12.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(n1_tan=Tan("n1"), n2_tan=Tan("n2")).first()
        self.assertIsInstance(obj.n1_tan, Decimal)
        self.assertIsInstance(obj.n2_tan, Decimal)
        self.assertAlmostEqual(obj.n1_tan, Decimal(math.tan(obj.n1)))
        self.assertAlmostEqual(obj.n2_tan, Decimal(math.tan(obj.n2)))
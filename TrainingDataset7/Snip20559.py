def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-12.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(n1_sin=Sin("n1"), n2_sin=Sin("n2")).first()
        self.assertIsInstance(obj.n1_sin, Decimal)
        self.assertIsInstance(obj.n2_sin, Decimal)
        self.assertAlmostEqual(obj.n1_sin, Decimal(math.sin(obj.n1)))
        self.assertAlmostEqual(obj.n2_sin, Decimal(math.sin(obj.n2)))
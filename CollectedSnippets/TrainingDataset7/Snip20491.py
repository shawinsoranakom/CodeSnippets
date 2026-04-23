def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-12.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(n1_cos=Cos("n1"), n2_cos=Cos("n2")).first()
        self.assertIsInstance(obj.n1_cos, Decimal)
        self.assertIsInstance(obj.n2_cos, Decimal)
        self.assertAlmostEqual(obj.n1_cos, Decimal(math.cos(obj.n1)))
        self.assertAlmostEqual(obj.n2_cos, Decimal(math.cos(obj.n2)))
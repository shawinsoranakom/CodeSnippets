def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("1.0"), n2=Decimal("-0.6"))
        obj = DecimalModel.objects.annotate(n_power=Power("n1", "n2")).first()
        self.assertIsInstance(obj.n_power, Decimal)
        self.assertAlmostEqual(obj.n_power, Decimal(obj.n1**obj.n2))
def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-12.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(
            n1_radians=Radians("n1"), n2_radians=Radians("n2")
        ).first()
        self.assertIsInstance(obj.n1_radians, Decimal)
        self.assertIsInstance(obj.n2_radians, Decimal)
        self.assertAlmostEqual(obj.n1_radians, Decimal(math.radians(obj.n1)))
        self.assertAlmostEqual(obj.n2_radians, Decimal(math.radians(obj.n2)))
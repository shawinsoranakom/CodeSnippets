def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-12.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(
            n1_degrees=Degrees("n1"), n2_degrees=Degrees("n2")
        ).first()
        self.assertIsInstance(obj.n1_degrees, Decimal)
        self.assertIsInstance(obj.n2_degrees, Decimal)
        self.assertAlmostEqual(obj.n1_degrees, Decimal(math.degrees(obj.n1)))
        self.assertAlmostEqual(obj.n2_degrees, Decimal(math.degrees(obj.n2)))
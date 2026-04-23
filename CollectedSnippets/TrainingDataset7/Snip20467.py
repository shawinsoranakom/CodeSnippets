def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-0.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(
            n1_acos=ACos("n1"), n2_acos=ACos("n2")
        ).first()
        self.assertIsInstance(obj.n1_acos, Decimal)
        self.assertIsInstance(obj.n2_acos, Decimal)
        self.assertAlmostEqual(obj.n1_acos, Decimal(math.acos(obj.n1)))
        self.assertAlmostEqual(obj.n2_acos, Decimal(math.acos(obj.n2)))
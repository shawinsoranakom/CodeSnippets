def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("12.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(
            n1_sqrt=Sqrt("n1"), n2_sqrt=Sqrt("n2")
        ).first()
        self.assertIsInstance(obj.n1_sqrt, Decimal)
        self.assertIsInstance(obj.n2_sqrt, Decimal)
        self.assertAlmostEqual(obj.n1_sqrt, Decimal(math.sqrt(obj.n1)))
        self.assertAlmostEqual(obj.n2_sqrt, Decimal(math.sqrt(obj.n2)))
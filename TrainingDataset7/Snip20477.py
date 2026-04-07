def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-12.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(
            n1_atan=ATan("n1"), n2_atan=ATan("n2")
        ).first()
        self.assertIsInstance(obj.n1_atan, Decimal)
        self.assertIsInstance(obj.n2_atan, Decimal)
        self.assertAlmostEqual(obj.n1_atan, Decimal(math.atan(obj.n1)))
        self.assertAlmostEqual(obj.n2_atan, Decimal(math.atan(obj.n2)))
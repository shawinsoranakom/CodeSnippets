def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-12.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(n1_exp=Exp("n1"), n2_exp=Exp("n2")).first()
        self.assertIsInstance(obj.n1_exp, Decimal)
        self.assertIsInstance(obj.n2_exp, Decimal)
        self.assertAlmostEqual(obj.n1_exp, Decimal(math.exp(obj.n1)))
        self.assertAlmostEqual(obj.n2_exp, Decimal(math.exp(obj.n2)))
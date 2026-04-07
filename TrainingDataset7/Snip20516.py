def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("12.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(n1_ln=Ln("n1"), n2_ln=Ln("n2")).first()
        self.assertIsInstance(obj.n1_ln, Decimal)
        self.assertIsInstance(obj.n2_ln, Decimal)
        self.assertAlmostEqual(obj.n1_ln, Decimal(math.log(obj.n1)))
        self.assertAlmostEqual(obj.n2_ln, Decimal(math.log(obj.n2)))
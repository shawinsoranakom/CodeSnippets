def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-0.8"), n2=Decimal("1.2"))
        obj = DecimalModel.objects.annotate(n1_abs=Abs("n1"), n2_abs=Abs("n2")).first()
        self.assertIsInstance(obj.n1_abs, Decimal)
        self.assertIsInstance(obj.n2_abs, Decimal)
        self.assertEqual(obj.n1, -obj.n1_abs)
        self.assertEqual(obj.n2, obj.n2_abs)
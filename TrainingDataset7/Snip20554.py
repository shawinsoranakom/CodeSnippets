def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-12.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(
            n1_sign=Sign("n1"), n2_sign=Sign("n2")
        ).first()
        self.assertIsInstance(obj.n1_sign, Decimal)
        self.assertIsInstance(obj.n2_sign, Decimal)
        self.assertEqual(obj.n1_sign, Decimal("-1"))
        self.assertEqual(obj.n2_sign, Decimal("1"))
def test_decimal_with_negative_precision(self):
        DecimalModel.objects.create(n1=Decimal("365.25"))
        obj = DecimalModel.objects.annotate(n1_round=Round("n1", -1)).first()
        self.assertIsInstance(obj.n1_round, Decimal)
        self.assertEqual(obj.n1_round, 370)
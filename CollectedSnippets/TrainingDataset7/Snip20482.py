def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-9.9"), n2=Decimal("4.6"))
        obj = DecimalModel.objects.annotate(n_atan2=ATan2("n1", "n2")).first()
        self.assertIsInstance(obj.n_atan2, Decimal)
        self.assertAlmostEqual(obj.n_atan2, Decimal(math.atan2(obj.n1, obj.n2)))
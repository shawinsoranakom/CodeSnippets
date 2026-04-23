def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("12.9"), n2=Decimal("3.6"))
        obj = DecimalModel.objects.annotate(n_log=Log("n1", "n2")).first()
        self.assertIsInstance(obj.n_log, Decimal)
        self.assertAlmostEqual(obj.n_log, Decimal(math.log(obj.n2, obj.n1)))
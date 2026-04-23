def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-9.9"), n2=Decimal("4.6"))
        obj = DecimalModel.objects.annotate(n_mod=Mod("n1", "n2")).first()
        self.assertIsInstance(obj.n_mod, Decimal)
        self.assertAlmostEqual(obj.n_mod, Decimal(math.fmod(obj.n1, obj.n2)))
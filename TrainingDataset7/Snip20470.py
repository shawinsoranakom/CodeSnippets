def test_transform(self):
        with register_lookup(DecimalField, ACos):
            DecimalModel.objects.create(n1=Decimal("0.5"), n2=Decimal("0"))
            DecimalModel.objects.create(n1=Decimal("-0.9"), n2=Decimal("0"))
            obj = DecimalModel.objects.filter(n1__acos__lt=2).get()
            self.assertEqual(obj.n1, Decimal("0.5"))
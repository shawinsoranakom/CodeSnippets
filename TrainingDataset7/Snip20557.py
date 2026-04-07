def test_transform(self):
        with register_lookup(DecimalField, Sign):
            DecimalModel.objects.create(n1=Decimal("5.4"), n2=Decimal("0"))
            DecimalModel.objects.create(n1=Decimal("-0.1"), n2=Decimal("0"))
            obj = DecimalModel.objects.filter(n1__sign__lt=0, n2__sign=0).get()
            self.assertEqual(obj.n1, Decimal("-0.1"))
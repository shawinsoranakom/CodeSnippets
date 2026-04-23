def test_transform(self):
        with register_lookup(DecimalField, Abs):
            DecimalModel.objects.create(n1=Decimal("-1.5"), n2=Decimal("0"))
            DecimalModel.objects.create(n1=Decimal("-0.5"), n2=Decimal("0"))
            obj = DecimalModel.objects.filter(n1__abs__gt=1).get()
            self.assertEqual(obj.n1, Decimal("-1.5"))
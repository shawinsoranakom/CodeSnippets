def test_transform(self):
        with register_lookup(DecimalField, Exp):
            DecimalModel.objects.create(n1=Decimal("12.0"), n2=Decimal("0"))
            DecimalModel.objects.create(n1=Decimal("-1.0"), n2=Decimal("0"))
            obj = DecimalModel.objects.filter(n1__exp__gt=10).get()
            self.assertEqual(obj.n1, Decimal("12.0"))
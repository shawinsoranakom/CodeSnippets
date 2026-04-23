def test_transform(self):
        with register_lookup(DecimalField, Round):
            DecimalModel.objects.create(n1=Decimal("2.0"), n2=Decimal("0"))
            DecimalModel.objects.create(n1=Decimal("-1.0"), n2=Decimal("0"))
            obj = DecimalModel.objects.filter(n1__round__gt=0).get()
            self.assertEqual(obj.n1, Decimal("2.0"))
def test_transform(self):
        with register_lookup(DecimalField, Degrees):
            DecimalModel.objects.create(n1=Decimal("5.4"), n2=Decimal("0"))
            DecimalModel.objects.create(n1=Decimal("-30"), n2=Decimal("0"))
            obj = DecimalModel.objects.filter(n1__degrees__gt=0).get()
            self.assertEqual(obj.n1, Decimal("5.4"))
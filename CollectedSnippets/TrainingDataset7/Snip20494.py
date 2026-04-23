def test_transform(self):
        with register_lookup(DecimalField, Cos):
            DecimalModel.objects.create(n1=Decimal("-8.0"), n2=Decimal("0"))
            DecimalModel.objects.create(n1=Decimal("3.14"), n2=Decimal("0"))
            obj = DecimalModel.objects.filter(n1__cos__gt=-0.2).get()
            self.assertEqual(obj.n1, Decimal("-8.0"))
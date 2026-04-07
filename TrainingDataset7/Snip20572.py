def test_transform(self):
        with register_lookup(DecimalField, Tan):
            DecimalModel.objects.create(n1=Decimal("0.0"), n2=Decimal("0"))
            DecimalModel.objects.create(n1=Decimal("12.0"), n2=Decimal("0"))
            obj = DecimalModel.objects.filter(n1__tan__lt=0).get()
            self.assertEqual(obj.n1, Decimal("12.0"))
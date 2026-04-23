def test_transform(self):
        with register_lookup(DecimalField, ASin):
            DecimalModel.objects.create(n1=Decimal("0.1"), n2=Decimal("0"))
            DecimalModel.objects.create(n1=Decimal("1.0"), n2=Decimal("0"))
            obj = DecimalModel.objects.filter(n1__asin__gt=1).get()
            self.assertEqual(obj.n1, Decimal("1.0"))
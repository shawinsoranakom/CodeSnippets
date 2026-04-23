def test_transform(self):
        with register_lookup(DecimalField, ATan):
            DecimalModel.objects.create(n1=Decimal("3.12"), n2=Decimal("0"))
            DecimalModel.objects.create(n1=Decimal("-5"), n2=Decimal("0"))
            obj = DecimalModel.objects.filter(n1__atan__gt=0).get()
            self.assertEqual(obj.n1, Decimal("3.12"))
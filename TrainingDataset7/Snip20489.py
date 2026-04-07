def test_transform(self):
        with register_lookup(DecimalField, Ceil):
            DecimalModel.objects.create(n1=Decimal("3.12"), n2=Decimal("0"))
            DecimalModel.objects.create(n1=Decimal("1.25"), n2=Decimal("0"))
            obj = DecimalModel.objects.filter(n1__ceil__gt=3).get()
            self.assertEqual(obj.n1, Decimal("3.12"))
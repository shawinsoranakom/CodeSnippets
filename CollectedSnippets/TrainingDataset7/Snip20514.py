def test_transform(self):
        with register_lookup(DecimalField, Floor):
            DecimalModel.objects.create(n1=Decimal("5.4"), n2=Decimal("0"))
            DecimalModel.objects.create(n1=Decimal("3.4"), n2=Decimal("0"))
            obj = DecimalModel.objects.filter(n1__floor__gt=4).get()
            self.assertEqual(obj.n1, Decimal("5.4"))
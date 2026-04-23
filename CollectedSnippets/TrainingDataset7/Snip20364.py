def test_decimal_filter(self):
        obj = DecimalModel.objects.create(n1=Decimal("1.1"), n2=Decimal("1.2"))
        self.assertCountEqual(
            DecimalModel.objects.annotate(
                least=Least("n1", "n2"),
            ).filter(least=Decimal("1.1")),
            [obj],
        )
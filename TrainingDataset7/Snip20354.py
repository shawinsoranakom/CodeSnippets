def test_decimal_filter(self):
        obj = DecimalModel.objects.create(n1=Decimal("1.1"), n2=Decimal("1.2"))
        self.assertCountEqual(
            DecimalModel.objects.annotate(
                greatest=Greatest("n1", "n2"),
            ).filter(greatest=Decimal("1.2")),
            [obj],
        )
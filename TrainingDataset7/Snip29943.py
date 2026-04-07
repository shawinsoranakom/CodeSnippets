def test_decimal_field_contained_by(self):
        objs = [
            RangeLookupsModel.objects.create(decimal_field=Decimal("1.33")),
            RangeLookupsModel.objects.create(decimal_field=Decimal("2.88")),
            RangeLookupsModel.objects.create(decimal_field=Decimal("99.17")),
        ]
        self.assertSequenceEqual(
            RangeLookupsModel.objects.filter(
                decimal_field__contained_by=NumericRange(
                    Decimal("1.89"), Decimal("7.91")
                ),
            ),
            [objs[1]],
        )
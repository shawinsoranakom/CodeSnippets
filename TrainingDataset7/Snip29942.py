def test_biginteger_range(self):
        objs = [
            RangeLookupsModel.objects.create(big_integer=5),
            RangeLookupsModel.objects.create(big_integer=99),
            RangeLookupsModel.objects.create(big_integer=-1),
        ]
        self.assertSequenceEqual(
            RangeLookupsModel.objects.filter(
                big_integer__contained_by=NumericRange(1, 98)
            ),
            [objs[0]],
        )
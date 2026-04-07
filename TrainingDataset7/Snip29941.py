def test_integer_range(self):
        objs = [
            RangeLookupsModel.objects.create(integer=5),
            RangeLookupsModel.objects.create(integer=99),
            RangeLookupsModel.objects.create(integer=-1),
        ]
        self.assertSequenceEqual(
            RangeLookupsModel.objects.filter(integer__contained_by=NumericRange(1, 98)),
            [objs[0]],
        )
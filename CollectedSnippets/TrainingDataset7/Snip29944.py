def test_float_range(self):
        objs = [
            RangeLookupsModel.objects.create(float=5),
            RangeLookupsModel.objects.create(float=99),
            RangeLookupsModel.objects.create(float=-1),
        ]
        self.assertSequenceEqual(
            RangeLookupsModel.objects.filter(float__contained_by=NumericRange(1, 98)),
            [objs[0]],
        )
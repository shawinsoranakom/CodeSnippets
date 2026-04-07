def test_exclude(self):
        objs = [
            RangeLookupsModel.objects.create(float=5),
            RangeLookupsModel.objects.create(float=99),
            RangeLookupsModel.objects.create(float=-1),
        ]
        self.assertSequenceEqual(
            RangeLookupsModel.objects.exclude(float__contained_by=NumericRange(0, 100)),
            [objs[2]],
        )
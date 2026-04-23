def test_f_ranges(self):
        parent = RangesModel.objects.create(decimals=NumericRange(0, 10))
        objs = [
            RangeLookupsModel.objects.create(float=5, parent=parent),
            RangeLookupsModel.objects.create(float=99, parent=parent),
        ]
        self.assertSequenceEqual(
            RangeLookupsModel.objects.filter(float__contained_by=F("parent__decimals")),
            [objs[0]],
        )
def test_small_integer_field_contained_by(self):
        objs = [
            RangeLookupsModel.objects.create(small_integer=8),
            RangeLookupsModel.objects.create(small_integer=4),
            RangeLookupsModel.objects.create(small_integer=-1),
        ]
        self.assertSequenceEqual(
            RangeLookupsModel.objects.filter(
                small_integer__contained_by=NumericRange(4, 6)
            ),
            [objs[1]],
        )
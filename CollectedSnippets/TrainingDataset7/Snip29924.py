def test_contains_range(self):
        self.assertSequenceEqual(
            RangesModel.objects.filter(ints__contains=NumericRange(3, 8)),
            [self.objs[0]],
        )
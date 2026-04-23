def test_not_gt(self):
        self.assertSequenceEqual(
            RangesModel.objects.filter(ints__not_gt=NumericRange(5, 10)),
            [self.objs[0], self.objs[2]],
        )
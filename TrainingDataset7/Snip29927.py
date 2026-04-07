def test_overlap(self):
        self.assertSequenceEqual(
            RangesModel.objects.filter(ints__overlap=NumericRange(3, 8)),
            [self.objs[0], self.objs[1]],
        )
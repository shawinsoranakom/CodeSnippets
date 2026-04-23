def test_adjacent_to(self):
        self.assertSequenceEqual(
            RangesModel.objects.filter(ints__adjacent_to=NumericRange(0, 5)),
            [self.objs[1], self.objs[2]],
        )
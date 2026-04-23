def test_startswith_chaining(self):
        self.assertSequenceEqual(
            RangesModel.objects.filter(ints__startswith__gte=0),
            [self.objs[0], self.objs[1]],
        )
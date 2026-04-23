def test_isnull(self):
        self.assertSequenceEqual(
            RangesModel.objects.filter(ints__isnull=True),
            [self.objs[4]],
        )
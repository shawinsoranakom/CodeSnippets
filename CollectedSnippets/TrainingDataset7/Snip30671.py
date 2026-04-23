def test_ordering(self):
        # Cross model ordering is possible in Meta, too.
        self.assertSequenceEqual(
            Ranking.objects.all(),
            [self.rank3, self.rank2, self.rank1],
        )
        self.assertSequenceEqual(
            Ranking.objects.order_by("rank"),
            [self.rank1, self.rank2, self.rank3],
        )
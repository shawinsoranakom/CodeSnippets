def test_rank_passing_untyped_args(self):
        searched = (
            Line.objects.filter(character=self.minstrel)
            .annotate(
                rank=SearchRank("dialogue", "brave sir robin"),
            )
            .order_by("rank")
        )
        self.assertSequenceEqual(searched, [self.verse2, self.verse1, self.verse0])
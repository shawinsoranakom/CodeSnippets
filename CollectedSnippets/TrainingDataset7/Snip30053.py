def test_ranking_with_normalization(self):
        short_verse = Line.objects.create(
            scene=self.robin,
            character=self.minstrel,
            dialogue="A brave retreat brave Sir Robin.",
        )
        searched = (
            Line.objects.filter(character=self.minstrel)
            .annotate(
                rank=SearchRank(
                    SearchVector("dialogue"),
                    SearchQuery("brave sir robin"),
                    # Divide the rank by the document length.
                    normalization=2,
                ),
            )
            .order_by("rank")
        )
        self.assertSequenceEqual(
            searched,
            [self.verse2, self.verse1, self.verse0, short_verse],
        )
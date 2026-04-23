def test_ranking_with_masked_normalization(self):
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
                    # Divide the rank by the document length and by the number
                    # of unique words in document.
                    normalization=Value(2).bitor(Value(8)),
                ),
            )
            .order_by("rank")
        )
        self.assertSequenceEqual(
            searched,
            [self.verse2, self.verse1, self.verse0, short_verse],
        )
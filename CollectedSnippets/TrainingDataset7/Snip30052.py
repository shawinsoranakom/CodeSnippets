def test_cover_density_ranking(self):
        not_dense_verse = Line.objects.create(
            scene=self.robin,
            character=self.minstrel,
            dialogue=(
                "Bravely taking to his feet, he beat a very brave retreat. "
                "A brave retreat brave Sir Robin."
            ),
        )
        searched = (
            Line.objects.filter(character=self.minstrel)
            .annotate(
                rank=SearchRank(
                    SearchVector("dialogue"),
                    SearchQuery("brave robin"),
                    cover_density=True,
                ),
            )
            .order_by("rank", "-pk")
        )
        self.assertSequenceEqual(
            searched,
            [self.verse2, not_dense_verse, self.verse1, self.verse0],
        )
def test_ranking(self):
        searched = (
            Line.objects.filter(character=self.minstrel)
            .annotate(
                rank=SearchRank(
                    SearchVector("dialogue"), SearchQuery("brave sir robin")
                ),
            )
            .order_by("rank")
        )
        self.assertSequenceEqual(searched, [self.verse2, self.verse1, self.verse0])
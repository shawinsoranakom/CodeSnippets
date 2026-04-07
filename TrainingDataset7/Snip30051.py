def test_ranking_chaining(self):
        searched = (
            Line.objects.filter(character=self.minstrel)
            .annotate(
                rank=SearchRank(
                    SearchVector("dialogue"), SearchQuery("brave sir robin")
                ),
            )
            .filter(rank__gt=0.3)
        )
        self.assertSequenceEqual(searched, [self.verse0])
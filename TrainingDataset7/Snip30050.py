def test_ranked_custom_weights(self):
        vector = SearchVector("dialogue", weight="D") + SearchVector(
            "character__name", weight="A"
        )
        weights = [1.0, 0.0, 0.0, 0.5]
        searched = (
            Line.objects.filter(scene=self.witch_scene)
            .annotate(
                rank=SearchRank(vector, SearchQuery("witch"), weights=weights),
            )
            .order_by("-rank")[:2]
        )
        self.assertSequenceEqual(searched, [self.crowd, self.witch])
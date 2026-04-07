def test_weights_in_vector(self):
        vector = SearchVector("dialogue", weight="A") + SearchVector(
            "character__name", weight="D"
        )
        searched = (
            Line.objects.filter(scene=self.witch_scene)
            .annotate(
                rank=SearchRank(vector, SearchQuery("witch")),
            )
            .order_by("-rank")[:2]
        )
        self.assertSequenceEqual(searched, [self.crowd, self.witch])

        vector = SearchVector("dialogue", weight="D") + SearchVector(
            "character__name", weight="A"
        )
        searched = (
            Line.objects.filter(scene=self.witch_scene)
            .annotate(
                rank=SearchRank(vector, SearchQuery("witch")),
            )
            .order_by("-rank")[:2]
        )
        self.assertSequenceEqual(searched, [self.witch, self.crowd])
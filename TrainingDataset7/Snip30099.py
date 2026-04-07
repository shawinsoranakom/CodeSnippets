def test_trigram_word_similarity_alternate(self):
        self.assertSequenceEqual(
            self.Model.objects.annotate(
                word_distance=TrigramWordDistance("mat", "field"),
            )
            .filter(
                word_distance__lte=0.7,
            )
            .values("field", "word_distance")
            .order_by("word_distance"),
            [
                {"field": "Cat sat on mat.", "word_distance": 0},
                {"field": "Matthew", "word_distance": 0.25},
            ],
        )
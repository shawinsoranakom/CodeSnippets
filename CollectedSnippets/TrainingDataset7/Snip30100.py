def test_trigram_strict_word_distance(self):
        self.assertSequenceEqual(
            self.Model.objects.annotate(
                word_distance=TrigramStrictWordDistance("matt", "field"),
            )
            .filter(word_distance__lte=0.7)
            .values("field", "word_distance")
            .order_by("word_distance"),
            [
                {"field": "Cat sat on mat.", "word_distance": 0.5},
                {"field": "Matthew", "word_distance": 0.5555556},
            ],
        )
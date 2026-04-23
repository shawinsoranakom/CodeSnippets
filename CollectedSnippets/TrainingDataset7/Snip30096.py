def test_trigram_word_similarity(self):
        search = "mat"
        self.assertSequenceEqual(
            self.Model.objects.filter(
                field__trigram_word_similar=search,
            )
            .annotate(
                word_similarity=TrigramWordSimilarity(search, "field"),
            )
            .values("field", "word_similarity")
            .order_by("-word_similarity"),
            [
                {"field": "Cat sat on mat.", "word_similarity": 1.0},
                {"field": "Matthew", "word_similarity": 0.75},
            ],
        )
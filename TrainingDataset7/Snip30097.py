def test_trigram_strict_word_similarity(self):
        search = "matt"
        self.assertSequenceEqual(
            self.Model.objects.filter(field__trigram_word_similar=search)
            .annotate(word_similarity=TrigramStrictWordSimilarity(search, "field"))
            .values("field", "word_similarity")
            .order_by("-word_similarity"),
            [
                {"field": "Cat sat on mat.", "word_similarity": 0.5},
                {"field": "Matthew", "word_similarity": 0.44444445},
            ],
        )
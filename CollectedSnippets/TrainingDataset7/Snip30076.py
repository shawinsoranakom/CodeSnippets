def test_lexemes_multiple_or(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(
            search=SearchQuery(
                Lexeme("kneecap", prefix=True) | Lexeme("afrai", prefix=True)
            )
        )

        self.assertSequenceEqual(searched, [self.verse0, self.verse1])
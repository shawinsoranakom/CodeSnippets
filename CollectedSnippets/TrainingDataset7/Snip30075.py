def test_lexemes_multiple_and(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(
            search=SearchQuery(
                Lexeme("Robi", prefix=True) & Lexeme("Camel", prefix=True)
            )
        )

        self.assertSequenceEqual(searched, [self.verse0])
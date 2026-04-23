def test_multiple_and(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(
            search=SearchQuery(
                Lexeme("bedemir") & Lexeme("scales") & Lexeme("nostrils")
            )
        )
        self.assertSequenceEqual(searched, [])

        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(search=SearchQuery(Lexeme("shall") & Lexeme("use") & Lexeme("larger")))
        self.assertSequenceEqual(searched, [self.bedemir0])
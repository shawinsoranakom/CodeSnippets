def test_and(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(search=SearchQuery(Lexeme("bedemir") & Lexeme("scales")))
        self.assertSequenceEqual(searched, [self.bedemir0])
def test_multiple_or(self):
        searched = Line.objects.annotate(search=SearchVector("dialogue")).filter(
            search=SearchQuery(
                Lexeme("kneecaps") | Lexeme("nostrils") | Lexeme("Sir Robin")
            )
        )
        self.assertCountEqual(searched, [self.verse1, self.verse2, self.verse0])
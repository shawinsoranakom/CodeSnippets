def test_or(self):
        searched = Line.objects.annotate(search=SearchVector("dialogue")).filter(
            search=SearchQuery(Lexeme("kneecaps") | Lexeme("nostrils"))
        )
        self.assertCountEqual(searched, [self.verse1, self.verse2])
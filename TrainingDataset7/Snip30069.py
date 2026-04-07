def test_invert(self):
        searched = Line.objects.annotate(search=SearchVector("dialogue")).filter(
            character=self.minstrel, search=SearchQuery(~Lexeme("kneecaps"))
        )
        self.assertCountEqual(searched, [self.verse0, self.verse2])
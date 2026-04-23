def test_advanced(self):
        """
        Combination of & and |
        This is mainly helpful for checking the test_advanced_invert below
        """
        searched = Line.objects.annotate(search=SearchVector("dialogue")).filter(
            search=SearchQuery(
                Lexeme("shall") & Lexeme("use") & Lexeme("larger") | Lexeme("nostrils")
            )
        )
        self.assertCountEqual(searched, [self.bedemir0, self.verse2])
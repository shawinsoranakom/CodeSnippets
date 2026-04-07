def test_advanced_invert(self):
        """
        Inverting a query that uses a combination of & and |
        should return the opposite of test_advanced.
        """
        searched = Line.objects.annotate(search=SearchVector("dialogue")).filter(
            search=SearchQuery(
                ~(
                    Lexeme("shall") & Lexeme("use") & Lexeme("larger")
                    | Lexeme("nostrils")
                )
            )
        )
        expected_result = Line.objects.exclude(
            id__in=[self.bedemir0.id, self.verse2.id]
        )
        self.assertCountEqual(searched, expected_result)
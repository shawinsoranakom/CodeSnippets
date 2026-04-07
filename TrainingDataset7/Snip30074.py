def test_inverse_prefix_searching(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(search=SearchQuery(Lexeme("Robi", prefix=True, invert=True)))
        self.assertEqual(
            set(searched),
            {
                self.verse2,
                self.bedemir0,
                self.bedemir1,
                self.french,
                self.crowd,
                self.witch,
                self.duck,
            },
        )
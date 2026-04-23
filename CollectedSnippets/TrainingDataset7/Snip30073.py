def test_prefix_searching(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(search=SearchQuery(Lexeme("hear", prefix=True)))

        self.assertSequenceEqual(searched, [self.verse2])
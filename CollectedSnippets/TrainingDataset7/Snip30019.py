def test_search_two_terms(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(search="heart forest")
        self.assertSequenceEqual(searched, [self.verse2])
def test_non_exact_match(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(search="heart")
        self.assertSequenceEqual(searched, [self.verse2])
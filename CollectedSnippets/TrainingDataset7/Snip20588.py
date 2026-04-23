def test_annotate(self):
        authors = Author.objects.annotate(
            first_initial=Left("name", 1),
            initial_chr=Chr(ord("J")),
        )
        self.assertSequenceEqual(
            authors.filter(first_initial=F("initial_chr")),
            [self.john],
        )
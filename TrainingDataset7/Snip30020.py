def test_terms_adjacent(self):
        searched = Line.objects.annotate(
            search=SearchVector("character__name", "dialogue"),
        ).filter(search="minstrel")
        self.assertCountEqual(searched, self.verses)
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(search="minstrelbravely")
        self.assertSequenceEqual(searched, [])
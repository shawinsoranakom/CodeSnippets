def test_query_and(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(search=SearchQuery("bedemir") & SearchQuery("scales"))
        self.assertSequenceEqual(searched, [self.bedemir0])
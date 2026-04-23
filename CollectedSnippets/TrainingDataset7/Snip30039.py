def test_query_multiple_and(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(
            search=SearchQuery("bedemir")
            & SearchQuery("scales")
            & SearchQuery("nostrils")
        )
        self.assertSequenceEqual(searched, [])

        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(
            search=SearchQuery("shall") & SearchQuery("use") & SearchQuery("larger")
        )
        self.assertSequenceEqual(searched, [self.bedemir0])
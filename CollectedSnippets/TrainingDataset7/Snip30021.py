def test_search_with_null(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(search="bedemir")
        self.assertCountEqual(
            searched, [self.bedemir0, self.bedemir1, self.crowd, self.witch, self.duck]
        )
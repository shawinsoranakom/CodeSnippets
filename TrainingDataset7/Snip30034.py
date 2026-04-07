def test_vector_add(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting") + SearchVector("character__name"),
        ).filter(search="bedemir")
        self.assertCountEqual(
            searched, [self.bedemir0, self.bedemir1, self.crowd, self.witch, self.duck]
        )
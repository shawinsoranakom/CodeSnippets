def test_vector_add_multi(self):
        searched = Line.objects.annotate(
            search=(
                SearchVector("scene__setting")
                + SearchVector("character__name")
                + SearchVector("dialogue")
            ),
        ).filter(search="bedemir")
        self.assertCountEqual(
            searched, [self.bedemir0, self.bedemir1, self.crowd, self.witch, self.duck]
        )
def test_simple_on_scene(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(search="Forest")
        self.assertCountEqual(searched, self.verses)
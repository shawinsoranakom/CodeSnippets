def test_simple_on_dialogue(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue"),
        ).filter(search="elbows")
        self.assertSequenceEqual(searched, [self.verse1])
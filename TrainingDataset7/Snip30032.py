def test_config_from_field_explicit(self):
        searched = Line.objects.annotate(
            search=SearchVector(
                "scene__setting", "dialogue", config=F("dialogue_config")
            ),
        ).filter(search=SearchQuery("cadeaux", config=F("dialogue_config")))
        self.assertSequenceEqual(searched, [self.french])
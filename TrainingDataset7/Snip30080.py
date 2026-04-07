def test_config_from_field_implicit(self):
        searched = Line.objects.annotate(
            search=SearchVector(
                "scene__setting", "dialogue", config=F("dialogue_config")
            ),
        ).filter(search=Lexeme("cadeaux"))
        self.assertSequenceEqual(searched, [self.french])
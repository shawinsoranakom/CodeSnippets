def test_phrase_search_with_config(self):
        line_qs = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue", config="french"),
        )
        searched = line_qs.filter(
            search=SearchQuery("cadeau beau un", search_type="phrase", config="french"),
        )
        self.assertSequenceEqual(searched, [])
        searched = line_qs.filter(
            search=SearchQuery("un beau cadeau", search_type="phrase", config="french"),
        )
        self.assertSequenceEqual(searched, [self.french])
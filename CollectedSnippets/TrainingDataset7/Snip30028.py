def test_web_search_with_config(self):
        line_qs = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue", config="french"),
        )
        searched = line_qs.filter(
            search=SearchQuery(
                "cadeau -beau", search_type="websearch", config="french"
            ),
        )
        self.assertSequenceEqual(searched, [])
        searched = line_qs.filter(
            search=SearchQuery("beau cadeau", search_type="websearch", config="french"),
        )
        self.assertSequenceEqual(searched, [self.french])
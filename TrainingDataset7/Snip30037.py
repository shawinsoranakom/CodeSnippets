def test_combine_different_vector_configs(self):
        self.check_default_text_search_config()
        searched = Line.objects.annotate(
            search=(
                SearchVector("dialogue", config="english")
                + SearchVector("dialogue", config="french")
            ),
        ).filter(
            search=SearchQuery("cadeaux", config="french") | SearchQuery("nostrils")
        )
        self.assertCountEqual(searched, [self.french, self.verse2])
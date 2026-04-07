def test_existing_vector_config_explicit(self):
        Line.objects.update(dialogue_search_vector=SearchVector("dialogue"))
        searched = Line.objects.filter(
            dialogue_search_vector=SearchQuery("cadeaux", config="french")
        )
        self.assertSequenceEqual(searched, [self.french])
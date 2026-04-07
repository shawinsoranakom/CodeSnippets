def test_existing_vector(self):
        Line.objects.update(dialogue_search_vector=SearchVector("dialogue"))
        searched = Line.objects.filter(
            dialogue_search_vector=SearchQuery("Robin killed")
        )
        self.assertSequenceEqual(searched, [self.verse0])
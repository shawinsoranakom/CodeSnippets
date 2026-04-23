def test_phrase_search(self):
        line_qs = Line.objects.annotate(search=SearchVector("dialogue"))
        searched = line_qs.filter(
            search=SearchQuery("burned body his away", search_type="phrase")
        )
        self.assertSequenceEqual(searched, [])
        searched = line_qs.filter(
            search=SearchQuery("his body burned away", search_type="phrase")
        )
        self.assertSequenceEqual(searched, [self.verse1])
def test_raw_search(self):
        line_qs = Line.objects.annotate(search=SearchVector("dialogue"))
        searched = line_qs.filter(search=SearchQuery("Robin", search_type="raw"))
        self.assertCountEqual(searched, [self.verse0, self.verse1])
        searched = line_qs.filter(
            search=SearchQuery("Robin & !'Camelot'", search_type="raw")
        )
        self.assertSequenceEqual(searched, [self.verse1])
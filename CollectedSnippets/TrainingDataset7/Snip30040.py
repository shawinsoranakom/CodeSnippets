def test_query_or(self):
        searched = Line.objects.filter(
            dialogue__search=SearchQuery("kneecaps") | SearchQuery("nostrils")
        )
        self.assertCountEqual(searched, [self.verse1, self.verse2])
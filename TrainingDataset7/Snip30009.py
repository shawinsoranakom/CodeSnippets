def test_search_query_config(self):
        searched = Line.objects.filter(
            dialogue__search=SearchQuery("nostrils", config="simple"),
        )
        self.assertSequenceEqual(searched, [self.verse2])
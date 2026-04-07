def test_query_multiple_or(self):
        searched = Line.objects.filter(
            dialogue__search=SearchQuery("kneecaps")
            | SearchQuery("nostrils")
            | SearchQuery("Sir Robin")
        )
        self.assertCountEqual(searched, [self.verse1, self.verse2, self.verse0])
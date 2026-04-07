def test_search_with_F_expression(self):
        # Non-matching query.
        LineSavedSearch.objects.create(line=self.verse1, query="hearts")
        # Matching query.
        match = LineSavedSearch.objects.create(line=self.verse1, query="elbows")
        for query_expression in [F("query"), SearchQuery(F("query"))]:
            with self.subTest(query_expression):
                searched = LineSavedSearch.objects.filter(
                    line__dialogue__search=query_expression,
                )
                self.assertSequenceEqual(searched, [match])
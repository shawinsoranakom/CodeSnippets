def test_web_search(self):
        line_qs = Line.objects.annotate(search=SearchVector("dialogue"))
        searched = line_qs.filter(
            search=SearchQuery(
                '"burned body" "split kneecaps"',
                search_type="websearch",
            ),
        )
        self.assertSequenceEqual(searched, [])
        searched = line_qs.filter(
            search=SearchQuery(
                '"body burned" "kneecaps split" -"nostrils"',
                search_type="websearch",
            ),
        )
        self.assertSequenceEqual(searched, [self.verse1])
        searched = line_qs.filter(
            search=SearchQuery(
                '"Sir Robin" ("kneecaps" OR "Camelot")',
                search_type="websearch",
            ),
        )
        self.assertSequenceEqual(searched, [self.verse0, self.verse1])
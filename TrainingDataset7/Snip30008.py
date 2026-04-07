def test_search_two_terms_with_partial_match(self):
        searched = Line.objects.filter(dialogue__search="Robin killed")
        self.assertSequenceEqual(searched, [self.verse0])
def test_query_invert(self):
        searched = Line.objects.filter(
            character=self.minstrel, dialogue__search=~SearchQuery("kneecaps")
        )
        self.assertCountEqual(searched, [self.verse0, self.verse2])
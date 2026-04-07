def test_raw_search_with_config(self):
        line_qs = Line.objects.annotate(
            search=SearchVector("dialogue", config="french")
        )
        searched = line_qs.filter(
            search=SearchQuery(
                "'cadeaux' & 'beaux'", search_type="raw", config="french"
            ),
        )
        self.assertSequenceEqual(searched, [self.french])
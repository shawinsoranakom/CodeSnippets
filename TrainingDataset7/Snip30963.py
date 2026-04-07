def test_rawqueryset_repr(self):
        queryset = RawQuerySet(raw_query="SELECT * FROM raw_query_author")
        self.assertEqual(
            repr(queryset), "<RawQuerySet: SELECT * FROM raw_query_author>"
        )
        self.assertEqual(
            repr(queryset.query), "<RawQuery: SELECT * FROM raw_query_author>"
        )
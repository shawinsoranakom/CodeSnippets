def test_str(self):
        tests = (
            (~SearchQuery("a"), "~SearchQuery(Value('a'))"),
            (
                (SearchQuery("a") | SearchQuery("b"))
                & (SearchQuery("c") | SearchQuery("d")),
                "((SearchQuery(Value('a')) || SearchQuery(Value('b'))) && "
                "(SearchQuery(Value('c')) || SearchQuery(Value('d'))))",
            ),
            (
                SearchQuery("a") & (SearchQuery("b") | SearchQuery("c")),
                "(SearchQuery(Value('a')) && (SearchQuery(Value('b')) || "
                "SearchQuery(Value('c'))))",
            ),
            (
                (SearchQuery("a") | SearchQuery("b")) & SearchQuery("c"),
                "((SearchQuery(Value('a')) || SearchQuery(Value('b'))) && "
                "SearchQuery(Value('c')))",
            ),
            (
                SearchQuery("a")
                & (SearchQuery("b") & (SearchQuery("c") | SearchQuery("d"))),
                "(SearchQuery(Value('a')) && (SearchQuery(Value('b')) && "
                "(SearchQuery(Value('c')) || SearchQuery(Value('d')))))",
            ),
        )
        for query, expected_str in tests:
            with self.subTest(query=query):
                self.assertEqual(str(query), expected_str)
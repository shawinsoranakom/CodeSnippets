def test_reverse_with_empty_query(self):
        cases = [None, "", {}, [], set(), (), QueryDict()]
        for query in cases:
            with self.subTest(query=query):
                self.assertEqual(reverse("test", query=query), "/test/1")
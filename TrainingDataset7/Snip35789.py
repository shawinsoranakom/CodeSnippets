def test_reverse_with_invalid_query(self):
        cases = [0, False, [1, 3, 5], {1, 2, 3}]
        for query in cases:
            with self.subTest(query=query):
                with self.assertRaises(TypeError):
                    print(reverse("test", query=query))
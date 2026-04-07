def test_reverse_with_query_from_querydict(self):
        query_string = "a=1&b=2&b=3&c=4"
        query_dict = QueryDict(query_string)
        self.assertEqual(reverse("test", query=query_dict), f"/test/1?{query_string}")
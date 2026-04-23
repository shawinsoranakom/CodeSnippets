def test_headers_as_iterable_of_tuple_pairs(self):
        response = HttpResponse(headers=(("X-Foo", "bar"),))
        self.assertEqual(response["X-Foo"], "bar")
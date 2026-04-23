def test_repr(self):
        response = HttpResponse(content="Café :)".encode(UTF8), status=201)
        expected = '<HttpResponse status_code=201, "text/html; charset=utf-8">'
        self.assertEqual(repr(response), expected)
def test_query_string_encoding(self):
        # WSGI requires latin-1 encoded strings.
        response = self.client.get("/get_view/?var=1\ufffd")
        self.assertEqual(response.context["var"], "1\ufffd")
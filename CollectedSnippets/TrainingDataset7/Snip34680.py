def test_request_factory_query_string(self):
        request = self.request_factory.get("/somewhere/", {"example": "data"})
        self.assertNotIn("Query-String", request.headers)
        self.assertEqual(request.GET["example"], "data")
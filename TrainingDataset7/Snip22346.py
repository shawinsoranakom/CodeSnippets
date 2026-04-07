def test_fallback_flatpage(self):
        "A fallback flatpage won't be served if the middleware is disabled"
        response = self.client.get("/flatpage/")
        self.assertEqual(response.status_code, 404)
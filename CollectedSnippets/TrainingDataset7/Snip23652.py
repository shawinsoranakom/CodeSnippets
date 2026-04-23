def test_content_type(self):
        response = self.client.get("/template/content_type/")
        self.assertEqual(response.headers["Content-Type"], "text/plain")
def test_non_html_response_encoding(self):
        response = self.client.get(
            "/raises500/", headers={"accept": "application/json"}
        )
        self.assertEqual(response.headers["Content-Type"], "text/plain; charset=utf-8")
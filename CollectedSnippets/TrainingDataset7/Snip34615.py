def test_unknown_page(self):
        "GET an invalid URL"
        response = self.client.get("/unknown_view/")

        # The response was a 404
        self.assertEqual(response.status_code, 404)
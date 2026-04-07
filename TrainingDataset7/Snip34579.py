def test_response_headers(self):
        "Check the value of HTTP headers returned in a response"
        response = self.client.get("/header_view/")

        self.assertEqual(response.headers["X-DJANGO-TEST"], "Slartibartfast")
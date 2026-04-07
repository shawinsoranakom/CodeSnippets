def test_redirect_with_http_host(self):
        response = self.client.get(
            "/redirect_to_different_hostname/", follow=True, HTTP_HOST="hostname1"
        )
        self.assertEqual(response.content, b"hostname2")
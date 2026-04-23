def test_client_headers_redirect(self):
        "Test client headers are preserved through redirects"
        response = self.client.get(
            "/check_headers_redirect/",
            follow=True,
            headers={"x-arg-check": "Testing 123"},
        )
        self.assertEqual(response.content, b"HTTP_X_ARG_CHECK: Testing 123")
        self.assertRedirects(
            response, "/check_headers/", status_code=302, target_status_code=200
        )
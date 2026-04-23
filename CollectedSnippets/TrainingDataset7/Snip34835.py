def test_client_headers(self):
        "A test client can receive custom headers"
        response = self.client.get(
            "/check_headers/", headers={"x-arg-check": "Testing 123"}
        )
        self.assertEqual(response.content, b"HTTP_X_ARG_CHECK: Testing 123")
        self.assertEqual(response.status_code, 200)
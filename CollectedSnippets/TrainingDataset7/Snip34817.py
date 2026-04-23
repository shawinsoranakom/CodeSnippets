def test_patch(self):
        "Request a view with string data via request method PATCH"
        # Regression test for #17797
        data = '{"test": "json"}'
        response = self.client.patch(
            "/request_methods/", data=data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"request method: PATCH")
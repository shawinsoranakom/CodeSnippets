def test_post(self):
        "Request a view with string data via request method POST"
        # Regression test for #11371
        data = '{"test": "json"}'
        response = self.client.post(
            "/request_methods/", data=data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"request method: POST")
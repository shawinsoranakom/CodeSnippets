def test_put(self):
        "Request a view with string data via request method PUT"
        # Regression test for #11371
        data = '{"test": "json"}'
        response = self.client.put(
            "/request_methods/", data=data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"request method: PUT")
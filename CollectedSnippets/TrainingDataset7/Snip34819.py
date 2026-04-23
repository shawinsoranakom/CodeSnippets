def test_json_bytes(self):
        response = self.client.post(
            "/body/", data=b"{'value': 37}", content_type="application/json"
        )
        self.assertEqual(response.content, b"{'value': 37}")
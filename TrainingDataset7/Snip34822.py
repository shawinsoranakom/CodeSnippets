def test_json_structured_suffixes(self):
        valid_types = (
            "application/vnd.api+json",
            "application/vnd.api.foo+json",
            "application/json; charset=utf-8",
            "application/activity+json",
            "application/activity+json; charset=utf-8",
        )
        for content_type in valid_types:
            response = self.client.get(
                "/json_response/", {"content_type": content_type}
            )
            self.assertEqual(response.headers["Content-Type"], content_type)
            self.assertEqual(response.json(), {"key": "value"})
def test_invalid_component_request(self):
        """Test request failure when invalid component name is provided."""

        response = self._request_component("invalid_component")
        self.assertEqual(404, response.code)
        self.assertEqual(b"not found", response.body)
def test_simple_payload(self):
        """A simple ASCII-only text can be POSTed."""
        text = "English: mountain pass"
        response = self.client.post(
            "/parse_encoded_text/", text, content_type="text/plain"
        )
        self.assertEqual(response.content, text.encode())
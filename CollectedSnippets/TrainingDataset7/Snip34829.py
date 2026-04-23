def test_utf16_payload(self):
        """Non-ASCII data encoded as UTF-16 can be POSTed."""
        text = "dog: собака"
        response = self.client.post(
            "/parse_encoded_text/", text, content_type="text/plain; charset=utf-16"
        )
        self.assertEqual(response.content, text.encode("utf-16"))
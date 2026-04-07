def test_utf8_payload(self):
        """Non-ASCII data encoded as UTF-8 can be POSTed."""
        text = "dog: собака"
        response = self.client.post(
            "/parse_encoded_text/", text, content_type="text/plain; charset=utf-8"
        )
        self.assertEqual(response.content, text.encode())
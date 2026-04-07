def test_non_utf_payload(self):
        """Non-ASCII data as a non-UTF based encoding can be POSTed."""
        text = "dog: собака"
        response = self.client.post(
            "/parse_encoded_text/", text, content_type="text/plain; charset=koi8-r"
        )
        self.assertEqual(response.content, text.encode("koi8-r"))
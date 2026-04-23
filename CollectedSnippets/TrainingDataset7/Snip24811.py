def test_unsafe_redirect(self):
        bad_urls = [
            'data:text/html,<script>window.alert("xss")</script>',
            "mailto:test@example.com",
            "file:///etc/passwd",
            "é" * (MAX_URL_REDIRECT_LENGTH + 1),
        ]
        for url in bad_urls:
            with self.assertRaises(DisallowedRedirect):
                HttpResponseRedirect(url)
            with self.assertRaises(DisallowedRedirect):
                HttpResponsePermanentRedirect(url)
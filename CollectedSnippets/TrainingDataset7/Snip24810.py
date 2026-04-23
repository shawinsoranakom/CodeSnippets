def test_redirect_url_max_length(self):
        base_url = "https://example.com/"
        for length in (
            MAX_URL_REDIRECT_LENGTH - 1,
            MAX_URL_REDIRECT_LENGTH,
        ):
            long_url = base_url + "x" * (length - len(base_url))
            with self.subTest(length=length):
                response = HttpResponseRedirect(long_url)
                self.assertEqual(response.url, long_url)
                response = HttpResponsePermanentRedirect(long_url)
                self.assertEqual(response.url, long_url)
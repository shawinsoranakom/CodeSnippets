def test_setlang_http_next(self):
        """
        The set_language view only redirects to the 'next' argument if it is
        "safe" and its scheme is HTTPS if the request was sent over HTTPS.
        """
        lang_code = self._get_inactive_language_code()
        non_https_next_url = "http://testserver/redirection/"
        post_data = {"language": lang_code, "next": non_https_next_url}
        # Insecure URL in POST data.
        response = self.client.post("/i18n/setlang/", data=post_data, secure=True)
        self.assertEqual(response.url, "/")
        self.assertEqual(
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, lang_code
        )
        # Insecure URL in HTTP referer.
        response = self.client.post(
            "/i18n/setlang/", secure=True, headers={"referer": non_https_next_url}
        )
        self.assertEqual(response.url, "/")
        self.assertEqual(
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, lang_code
        )
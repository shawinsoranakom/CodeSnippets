def test_setlang_unsafe_next(self):
        """
        The set_language view only redirects to the 'next' argument if it is
        "safe".
        """
        lang_code = self._get_inactive_language_code()
        post_data = {"language": lang_code, "next": "//unsafe/redirection/"}
        response = self.client.post("/i18n/setlang/", data=post_data)
        self.assertEqual(response.url, "/")
        self.assertEqual(
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, lang_code
        )
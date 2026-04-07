def test_setlang_default_redirect(self):
        """
        The set_language view redirects to '/' when there isn't a referer or
        "next" parameter.
        """
        lang_code = self._get_inactive_language_code()
        post_data = {"language": lang_code}
        response = self.client.post("/i18n/setlang/", post_data)
        self.assertRedirects(response, "/")
        self.assertEqual(
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, lang_code
        )
def test_setlang_redirect_to_referer(self):
        """
        The set_language view redirects to the URL in the referer header when
        there isn't a "next" parameter.
        """
        lang_code = self._get_inactive_language_code()
        post_data = {"language": lang_code}
        response = self.client.post(
            "/i18n/setlang/", post_data, headers={"referer": "/i18n/"}
        )
        self.assertRedirects(response, "/i18n/", fetch_redirect_response=False)
        self.assertEqual(
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, lang_code
        )
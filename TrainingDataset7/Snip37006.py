def test_setlang(self):
        """
        The set_language view can be used to change the session language.

        The user is redirected to the 'next' argument if provided.
        """
        lang_code = self._get_inactive_language_code()
        post_data = {"language": lang_code, "next": "/"}
        response = self.client.post(
            "/i18n/setlang/", post_data, headers={"referer": "/i_should_not_be_used/"}
        )
        self.assertRedirects(response, "/")
        # The language is set in a cookie.
        language_cookie = self.client.cookies[settings.LANGUAGE_COOKIE_NAME]
        self.assertEqual(language_cookie.value, lang_code)
        self.assertEqual(language_cookie["domain"], "")
        self.assertEqual(language_cookie["path"], "/")
        self.assertEqual(language_cookie["max-age"], "")
        self.assertEqual(language_cookie["httponly"], "")
        self.assertEqual(language_cookie["samesite"], "")
        self.assertEqual(language_cookie["secure"], "")
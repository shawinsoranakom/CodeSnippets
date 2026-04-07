def test_setlang_unsafe_next_for_ajax(self):
        """
        The fallback to root URL for the set_language view works for requests
        not accepting HTML response content.
        """
        lang_code = self._get_inactive_language_code()
        post_data = {"language": lang_code, "next": "//unsafe/redirection/"}
        response = self.client.post(
            "/i18n/setlang/", post_data, headers={"accept": "application/json"}
        )
        self.assertEqual(response.url, "/")
        self.assertEqual(
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, lang_code
        )
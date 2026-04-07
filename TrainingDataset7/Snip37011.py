def test_setlang_performs_redirect_for_ajax_if_explicitly_requested(self):
        """
        The set_language view redirects to the "next" parameter for requests
        not accepting HTML response content.
        """
        lang_code = self._get_inactive_language_code()
        post_data = {"language": lang_code, "next": "/"}
        response = self.client.post(
            "/i18n/setlang/", post_data, headers={"accept": "application/json"}
        )
        self.assertRedirects(response, "/")
        self.assertEqual(
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, lang_code
        )
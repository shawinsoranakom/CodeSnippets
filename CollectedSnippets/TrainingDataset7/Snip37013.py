def test_setlang_doesnt_perform_a_default_redirect_for_ajax(self):
        """
        The set_language view returns 204 by default for requests not accepting
        HTML response content.
        """
        lang_code = self._get_inactive_language_code()
        post_data = {"language": lang_code}
        response = self.client.post(
            "/i18n/setlang/", post_data, headers={"accept": "application/json"}
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, lang_code
        )
def test_setlang_doesnt_perform_a_redirect_to_referer_for_ajax(self):
        """
        The set_language view doesn't redirect to the HTTP referer header if
        the request doesn't accept HTML response content.
        """
        lang_code = self._get_inactive_language_code()
        post_data = {"language": lang_code}
        headers = {"HTTP_REFERER": "/", "HTTP_ACCEPT": "application/json"}
        response = self.client.post("/i18n/setlang/", post_data, **headers)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, lang_code
        )
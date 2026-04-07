def test_setlang_decodes_http_referer_url(self):
        """
        The set_language view decodes the HTTP_REFERER URL and preserves an
        encoded query string.
        """
        # The URL & view must exist for this to work as a regression test.
        self.assertEqual(
            reverse("with_parameter", kwargs={"parameter": "x"}), "/test-setlang/x/"
        )
        lang_code = self._get_inactive_language_code()
        # %C3%A4 decodes to ä, %26 to &.
        encoded_url = "/test-setlang/%C3%A4/?foo=bar&baz=alpha%26omega"
        response = self.client.post(
            "/i18n/setlang/", {"language": lang_code}, headers={"referer": encoded_url}
        )
        self.assertRedirects(response, encoded_url, fetch_redirect_response=False)
        self.assertEqual(
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, lang_code
        )
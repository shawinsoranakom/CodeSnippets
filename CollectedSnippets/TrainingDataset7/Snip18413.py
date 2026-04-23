def test_security_check_https(self):
        logout_url = reverse("logout")
        non_https_next_url = "http://testserver/"
        url = "%(url)s?%(next)s=%(next_url)s" % {
            "url": logout_url,
            "next": REDIRECT_FIELD_NAME,
            "next_url": quote(non_https_next_url),
        }
        self.login()
        response = self.client.post(url, secure=True)
        self.assertRedirects(response, logout_url, fetch_redirect_response=False)
        self.confirm_logged_out()
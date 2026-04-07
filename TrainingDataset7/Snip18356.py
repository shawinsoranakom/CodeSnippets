def test_security_check_https(self):
        login_url = reverse("login")
        non_https_next_url = "http://testserver/path"
        not_secured_url = "%(url)s?%(next)s=%(next_url)s" % {
            "url": login_url,
            "next": REDIRECT_FIELD_NAME,
            "next_url": quote(non_https_next_url),
        }
        post_data = {
            "username": "testclient",
            "password": "password",
        }
        response = self.client.post(not_secured_url, post_data, secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(response.url, non_https_next_url)
        self.assertEqual(response.url, settings.LOGIN_REDIRECT_URL)
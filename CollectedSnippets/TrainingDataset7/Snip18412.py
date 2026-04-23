def test_security_check(self):
        logout_url = reverse("logout")

        # These URLs should not pass the security check.
        bad_urls = (
            "http://example.com",
            "http:///example.com",
            "https://example.com",
            "ftp://example.com",
            "///example.com",
            "//example.com",
            'javascript:alert("XSS")',
        )
        for bad_url in bad_urls:
            with self.subTest(bad_url=bad_url):
                nasty_url = "%(url)s?%(next)s=%(bad_url)s" % {
                    "url": logout_url,
                    "next": REDIRECT_FIELD_NAME,
                    "bad_url": quote(bad_url),
                }
                self.login()
                response = self.client.post(nasty_url)
                self.assertEqual(response.status_code, 302)
                self.assertNotIn(
                    bad_url, response.url, "%s should be blocked" % bad_url
                )
                self.confirm_logged_out()

        # These URLs should pass the security check.
        good_urls = (
            "/view/?param=http://example.com",
            "/view/?param=https://example.com",
            "/view?param=ftp://example.com",
            "view/?param=//example.com",
            "https://testserver/",
            "HTTPS://testserver/",
            "//testserver/",
            "/url%20with%20spaces/",
        )
        for good_url in good_urls:
            with self.subTest(good_url=good_url):
                safe_url = "%(url)s?%(next)s=%(good_url)s" % {
                    "url": logout_url,
                    "next": REDIRECT_FIELD_NAME,
                    "good_url": quote(good_url),
                }
                self.login()
                response = self.client.post(safe_url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(good_url, response.url, "%s should be allowed" % good_url)
                self.confirm_logged_out()
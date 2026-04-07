def test_https_good_referer_matches_cookie_domain(self):
        """
        A POST HTTPS request with a good referer should be accepted from a
        subdomain that's allowed by SESSION_COOKIE_DOMAIN.
        """
        self._test_https_good_referer_matches_cookie_domain()
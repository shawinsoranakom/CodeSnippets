def test_https_malformed_host(self):
        """
        CsrfViewMiddleware generates a 403 response if it receives an HTTPS
        request with a bad host.
        """
        req = self._get_request(method="POST")
        req._is_secure_override = True
        req.META["HTTP_HOST"] = "@malformed"
        req.META["HTTP_REFERER"] = "https://www.evil.org/somepage"
        req.META["SERVER_PORT"] = "443"
        mw = CsrfViewMiddleware(token_view)
        expected = (
            "Referer checking failed - https://www.evil.org/somepage does not "
            "match any trusted origins."
        )
        with self.assertRaisesMessage(RejectRequest, expected):
            mw._check_referer(req)
        response = mw.process_view(req, token_view, (), {})
        self.assertEqual(response.status_code, 403)
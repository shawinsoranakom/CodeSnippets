def test_origin_malformed_host(self):
        req = self._get_request(method="POST")
        req._is_secure_override = True
        req.META["HTTP_HOST"] = "@malformed"
        req.META["HTTP_ORIGIN"] = "https://www.evil.org"
        mw = CsrfViewMiddleware(token_view)
        self._check_referer_rejects(mw, req)
        response = mw.process_view(req, token_view, (), {})
        self.assertEqual(response.status_code, 403)
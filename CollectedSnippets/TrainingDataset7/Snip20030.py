def test_https_malformed_referer(self):
        """
        A POST HTTPS request with a bad referer is rejected.
        """
        malformed_referer_msg = "Referer checking failed - Referer is malformed."
        req = self._get_POST_request_with_token()
        req._is_secure_override = True
        req.META["HTTP_REFERER"] = "http://http://www.example.com/"
        mw = CsrfViewMiddleware(post_form_view)
        self._check_referer_rejects(mw, req)
        response = mw.process_view(req, post_form_view, (), {})
        self.assertContains(
            response,
            "Referer checking failed - Referer is insecure while host is secure.",
            status_code=403,
        )
        # Empty
        req.META["HTTP_REFERER"] = ""
        self._check_referer_rejects(mw, req)
        response = mw.process_view(req, post_form_view, (), {})
        self.assertContains(response, malformed_referer_msg, status_code=403)
        # Non-ASCII
        req.META["HTTP_REFERER"] = "ØBöIß"
        self._check_referer_rejects(mw, req)
        response = mw.process_view(req, post_form_view, (), {})
        self.assertContains(response, malformed_referer_msg, status_code=403)
        # missing scheme
        # >>> urlsplit('//example.com/')
        # SplitResult(scheme='', netloc='example.com', path='/', query='',
        # fragment='')
        req.META["HTTP_REFERER"] = "//example.com/"
        self._check_referer_rejects(mw, req)
        response = mw.process_view(req, post_form_view, (), {})
        self.assertContains(response, malformed_referer_msg, status_code=403)
        # missing netloc
        # >>> urlsplit('https://')
        # SplitResult(scheme='https', netloc='', path='', query='',
        # fragment='')
        req.META["HTTP_REFERER"] = "https://"
        self._check_referer_rejects(mw, req)
        response = mw.process_view(req, post_form_view, (), {})
        self.assertContains(response, malformed_referer_msg, status_code=403)
        # Invalid URL
        # >>> urlsplit('https://[')
        # ValueError: Invalid IPv6 URL
        req.META["HTTP_REFERER"] = "https://["
        self._check_referer_rejects(mw, req)
        response = mw.process_view(req, post_form_view, (), {})
        self.assertContains(response, malformed_referer_msg, status_code=403)